import sys
from functools import partial
from importlib import import_module
from multiprocessing import Pool
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import pandas
from torch.autograd import Variable
from torch.backends import cudnn
from torch.nn import DataParallel
from torch.utils.data import DataLoader

from DSB2017.layers import nms
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

import os

os.environ["LRU_CACHE_CAPACITY"] = "1"

use_gpu = config_submit['n_gpu'] > 0
if not use_gpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)

# Additional Info when using cuda
if device.type == 'cuda':
    print(torch.cuda.get_device_name(0))
    print('Memory Usage:')
    print('Allocated:', round(torch.cuda.memory_allocated(0) / 1024 ** 3, 1), 'GB')
    print('Cached:   ', round(torch.cuda.memory_cached(0) / 1024 ** 3, 1), 'GB')

skip_prep = config_submit['skip_preprocessing']
skip_detect = config_submit['skip_detect']
sidelen = 144


def test_casenet(model, testset):
    data_loader = DataLoader(
        testset,
        batch_size=1,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=use_gpu)
    if use_gpu:
        model = model.cuda()
    model.eval()
    predlist = []

    # weight = torch.from_numpy(np.ones_like(y).float().cuda()
    for i, (x, coord) in enumerate(data_loader):

        coord = Variable(coord)
        x = Variable(x)
        if use_gpu:
            coord = coord.cuda()
            x = x.cuda()
        nodulePred, casePred, _ = model(x, coord)
        predlist.append(casePred.data.cpu().numpy())
        # print([i,data_loader.dataset.split[i,1],casePred.data.cpu().numpy()])
    predlist = np.concatenate(predlist)
    return predlist


def inference(input_path, output_file=None):
    output_filename = os.path.splitext(os.path.basename(input_path))[0] if output_file is None else output_file

    if os.path.isfile(input_path) and input_path.endswith('mhd'):
        prep_result_path = bbox_result_path = Path(input_path).parent
        testsplit = [input_path]
        preprocess_mhd(input_path, save_to_file=True)
        if output_file is None:
            output_file = os.path.join(prep_result_path, f'{output_filename}.csv')

    elif os.path.isdir(input_path):
        if output_file is None:
            output_file = os.path.join(input_path, f'{output_filename}.csv')
        prep_result_path = bbox_result_path = input_path
        n_worker = config_submit['n_worker_preprocessing']
        pool = Pool(n_worker)
        from fnmatch import fnmatch

        mhd_files = []

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
        else:
            # Preprocess DCM files
            testsplit = full_prep(input_path, prep_result_path, n_worker=config.num_workers, use_existing=False)

    else:
        raise ValueError('Input a mhd file or a mhd/dicom directory!')

    nodmodel = import_module(config_submit['detector_model'].split('.py')[0])
    config1, nod_net, loss, get_pbb = nodmodel.get_model()
    checkpoint = torch.load(config_submit['detector_param'])
    nod_net.load_state_dict(checkpoint['state_dict'])

    if use_gpu:
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
                                 shuffle=False, num_workers=config.num_workers, pin_memory=use_gpu, collate_fn=collate)

        test_detect(test_loader, nod_net, get_pbb, bbox_result_path, config1, n_gpu=config_submit['n_gpu'])

    casemodel = import_module(config_submit['classifier_model'].split('.py')[0])
    casenet = casemodel.CaseNet(topk=5)
    config2 = casemodel.config
    checkpoint = torch.load(config_submit['classifier_param'], encoding='latin1')
    casenet.load_state_dict(checkpoint['state_dict'])

    if use_gpu:
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
    return predlist


def make_bb_image(slice_mat, bb_mat, output_img_file=None):
    img = np.load(slice_mat)
    pbb = np.load(bb_mat)

    pbb = pbb[pbb[:, 0] > -1]

    pbb = nms(pbb, 0.05)
    box = pbb[0].astype('int')[1:]

    single_slice = img[0, box[0]]
    # print(single_slice.shape)
    single_slice = cv2.rectangle(single_slice, (box[2] - box[3], box[1] - box[3]), (box[2] + box[3], box[1] + box[3]),
                                 color=(0, 0, 255))
    plt.imshow(single_slice, cmap='binary')

    output_img_file = os.path.splitext(os.path.basename(bb_mat))[0] if output_img_file is None else output_img_file
    output_img_file = output_img_file.replace('_pbb', '') + '.png'

    output_img_file_path = os.path.join(Path(slice_mat).parent, output_img_file)

    plt.imsave(output_img_file_path, single_slice, cmap='binary')
    print('Write bb to img:', output_img_file)
    return output_img_file


if __name__ == "__main__":

    mhd = ['/home/vantuan5644/PycharmProjects/dataset/dataset_luna/', '1.3.6.1.4.1.14519.5.2.1.6279.6001.100684836163890911914061745866', '.mhd']
    inference(input_path=''.join(mhd))

    # sao cai file mhd bi hard code o day?
    # cai main nay ko chay dau thay. cai nay la de test thoi a. em imort tu main r call cai ham inference
    make_bb_image(''.join([mhd[0], mhd[1], '_clean.npy']), ''.join([mhd[0], mhd[1], '_pbb.npy']))
