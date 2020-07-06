import time

import torch
from torch.autograd import Variable

from DSB2017.config import config_submit
from DSB2017.utils import *

sidelen = 144
use_gpu = config_submit['n_gpu'] > 0


def test_detect(data_loader, net, get_pbb, save_dir, config, n_gpu):
    start_time = time.time()
    net.eval()
    split_comber = data_loader.dataset.split_comber
    for i_name, (data, target, coord, nzhw) in enumerate(data_loader):
        s = time.time()
        save_dir = os.path.split(data_loader.dataset.filenames[i_name])[0]
        target = [np.asarray(t, np.float32) for t in target]
        lbb = target[0]
        nzhw = nzhw[0]
        name = data_loader.dataset.filenames[i_name].split('-')[0].split('/')[-1]
        shortname = name.split('_clean')[0]
        data = data[0][0]
        coord = coord[0][0]
        isfeat = False
        if 'output_feature' in config:
            if config['output_feature']:
                isfeat = True
        n_per_run = n_gpu
        print(data.size())
        if use_gpu:
            splitlist = range(0, len(data) + 1, n_gpu)
        else:
            splitlist = range(0, len(data) + 1)
        if splitlist[-1] != len(data):
            splitlist.append(len(data))
        outputlist = []
        featurelist = []
        with torch.no_grad():
            for i in range(len(splitlist) - 1):
                input = Variable(data[splitlist[i]:splitlist[i + 1]])
                inputcoord = Variable(coord[splitlist[i]:splitlist[i + 1]])
                if use_gpu:
                    input = input.cuda()
                    inputcoord = inputcoord.cuda()

                if isfeat:
                    output, feature = net(input, inputcoord)
                    featurelist.append(feature.data.cpu().numpy())

                else:
                    output = net(input, inputcoord)
                outputlist.append(output.data.cpu().numpy())
        output = np.concatenate(outputlist, 0)
        output = split_comber.combine(output, nzhw=nzhw)
        if isfeat:
            feature = np.concatenate(featurelist, 0).transpose([0, 2, 3, 4, 1])[:, :, :, :, :, np.newaxis]
            feature = split_comber.combine(feature, sidelen)[..., 0]

        thresh = -3
        pbb, mask = get_pbb(output, thresh, ismask=True)
        if isfeat:
            feature_selected = feature[mask[0], mask[1], mask[2]]
            np.save(os.path.join(save_dir, shortname + '_feature.npy'), feature_selected)
        # tp,fp,fn,_ = acc(pbb,lbb,0,0.1,0.1)
        # print([len(tp),len(fp),len(fn)])
        print([i_name, shortname])
        e = time.time()

        np.save(os.path.join(save_dir, shortname + '_pbb.npy'), pbb)
        np.save(os.path.join(save_dir, shortname + '_lbb.npy'), lbb)
    end_time = time.time()

    print('elapsed time is %3.2f seconds' % (end_time - start_time))
