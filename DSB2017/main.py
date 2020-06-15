import sys
from functools import partial
from importlib import import_module
from multiprocessing import Pool
from pathlib import Path

import pandas
from torch.autograd import Variable
from torch.backends import cudnn
from torch.nn import DataParallel
from torch.utils.data import DataLoader

from DSB2017.preprocessing.full_prep import full_prep

sys.path.append('..')
from DSB2017 import config
from DSB2017.config import config_submit
from DSB2017.data_classifier import DataBowl3Classifier
from DSB2017.data_detector import DataBowl3Detector, collate
from DSB2017.preprocessing.prep_testing import preprocess_mhd
from DSB2017.split_combine import SplitComb
from DSB2017.test_detect import test_detect
from DSB2017.utils import *

# parser = argparse.ArgumentParser(description='DSB2017 inference')
# parser.add_argument('--input', '-i', type=str,
#                     help='Path to mhd file or the dir that contains multiple scans')
# parser.add_argument('--output_file', '-o', type=str, default='prediction.csv',
#                     help='Path to the csv output log')
# args = parser.parse_args()

skip_prep = config_submit['skip_preprocessing']
skip_detect = config_submit['skip_detect']
sidelen = 144


def test_casenet(model, testset):
    data_loader = DataLoader(
        testset,
        batch_size=1,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=True)
    # model = model.cuda()
    model.eval()
    predlist = []

    #     weight = torch.from_numpy(np.ones_like(y).float().cuda()
    for i, (x, coord) in enumerate(data_loader):
        coord = Variable(coord).cuda()
        x = Variable(x).cuda()
        nodulePred, casePred, _ = model(x, coord)
        predlist.append(casePred.data.cpu().numpy())
        # print([i,data_loader.dataset.split[i,1],casePred.data.cpu().numpy()])
    predlist = np.concatenate(predlist)
    return predlist


def inference(input_path, output_file=None):
    if os.path.isfile(input_path) and input_path.endswith('mhd'):
        prep_result_path = bbox_result_path = Path(input_path).parent
        testsplit = [input_path]
        preprocess_mhd(input_path, save_to_file=True)
        if output_file is None:
            output_file = os.path.join(prep_result_path, 'prediction.csv')

    elif os.path.isdir(input_path):
        if output_file is None:
            output_file = os.path.join(input_path, 'prediction.csv')
        prep_result_path = bbox_result_path = input_path
        n_worker = config_submit['n_worker_preprocessing']
        pool = Pool(n_worker)
        from fnmatch import fnmatch

        mhd_files = []
        dcm_dirs = []

        for path, subdirs, files in os.walk(input_path):
            for name in files:
                if fnmatch(name, "*.mhd"):
                    mhd_files.append(os.path.join(path, name))

        if len(mhd_files) > 0:
            testsplit = mhd_files
            partial_preprocess = partial(preprocess_mhd, save_to_file=True)

            # N = len(mhd_files)
            _ = pool.map(partial_preprocess, mhd_files)
            pool.close()
            pool.join()

        # Preprocess DCM files
        testsplit = full_prep(input_path, prep_result_path, n_worker=config.num_workers)

    else:
        raise ValueError('Input a mhd file or a mhd directory!')

    nodmodel = import_module(config_submit['detector_model'].split('.py')[0])
    config1, nod_net, loss, get_pbb = nodmodel.get_model()
    checkpoint = torch.load(config_submit['detector_param'])
    nod_net.load_state_dict(checkpoint['state_dict'])

    torch.cuda.set_device(0)
    nod_net = nod_net.cuda()
    cudnn.benchmark = True
    nod_net = DataParallel(nod_net)

    if not skip_detect:
        margin = 32
        sidelen = 144
        config1['datadir'] = prep_result_path
        split_comber = SplitComb(sidelen, config1['max_stride'], config1['stride'], margin,
                                 pad_value=config1['pad_value'])

        dataset = DataBowl3Detector(testsplit, config1, phase='test', split_comber=split_comber)
        test_loader = DataLoader(dataset, batch_size=1,
                                 shuffle=False, num_workers=config.num_workers, pin_memory=False, collate_fn=collate)

        test_detect(test_loader, nod_net, get_pbb, bbox_result_path, config1, n_gpu=config_submit['n_gpu'])

    casemodel = import_module(config_submit['classifier_model'].split('.py')[0])
    casenet = casemodel.CaseNet(topk=5)
    config2 = casemodel.config
    checkpoint = torch.load(config_submit['classifier_param'], encoding='latin1')
    casenet.load_state_dict(checkpoint['state_dict'])

    torch.cuda.set_device(0)
    casenet = casenet.cuda()
    cudnn.benchmark = True
    casenet = DataParallel(casenet)
    config2['bboxpath'] = bbox_result_path
    config2['datadir'] = prep_result_path

    dataset = DataBowl3Classifier(testsplit, config2, phase='test')
    predlist = test_casenet(casenet, dataset).T

    print('Predictions:', predlist)
    df = pandas.DataFrame({'filepath': testsplit, 'cancer': predlist})
    print('Output log wrote to file:', output_file)
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    inference(input_path='/home/vantuan5644/PycharmProjects/DSB3_/test')
