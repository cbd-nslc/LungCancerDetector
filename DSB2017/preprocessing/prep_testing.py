import os

import numpy as np

from DSB2017.preprocessing.full_prep import process_mask, lumTrans, resample
from DSB2017.training.prepare import load_itk_image


def preprocess_mhd(mhd_file, save_to_file=False, save_to_dir=None):
    file_name = os.path.splitext(mhd_file)[0]
    resolution = np.array([1, 1, 1])
    #     resolution = np.array([2,2,2])

    Mask, origin, spacing, isflip = load_itk_image(mhd_file)
    if isflip:
        Mask = Mask[:, ::-1, ::-1]
    newshape = np.round(np.array(Mask.shape) * spacing / resolution).astype('int')
    m1 = Mask == 3
    m2 = Mask == 4
    Mask = m1 + m2
    xx, yy, zz = np.where(Mask)
    box = np.array([[np.min(xx), np.max(xx)], [np.min(yy), np.max(yy)], [np.min(zz), np.max(zz)]])
    box = box * np.expand_dims(spacing, 1) / np.expand_dims(resolution, 1)
    box = np.floor(box).astype('int')
    margin = 5
    extendbox = np.vstack(
        [np.max([[0, 0, 0], box[:, 0] - margin], 0), np.min([newshape, box[:, 1] + 2 * margin], axis=0).T]).T

    # Save slices
    dm1 = process_mask(m1)
    dm2 = process_mask(m2)
    dilatedMask = dm1 + dm2
    Mask = m1 + m2
    extramask = dilatedMask ^ Mask
    bone_thresh = 210
    pad_value = 170

    sliceim, origin, spacing, isflip = load_itk_image(mhd_file)
    if isflip:
        sliceim = sliceim[:, ::-1, ::-1]
        print('flip!')
    sliceim = lumTrans(sliceim)
    sliceim = sliceim * dilatedMask + pad_value * (1 - dilatedMask).astype('uint8')
    bones = (sliceim * extramask) > bone_thresh
    sliceim[bones] = pad_value

    sliceim1, _ = resample(sliceim, spacing, resolution, order=1)
    sliceim2 = sliceim1[extendbox[0, 0]:extendbox[0, 1],
               extendbox[1, 0]:extendbox[1, 1],
               extendbox[2, 0]:extendbox[2, 1]]
    sliceim = sliceim2[np.newaxis, ...]
    if save_to_file:
        if save_to_dir is None:
            save_to_dir = os.path.split(mhd_file)[0]
        np.save(os.path.join(save_to_dir, file_name + '_clean.npy'), sliceim)
        label2 = np.array([[0, 0, 0, 0]])
        np.save(os.path.join(save_to_dir, file_name + '_label.npy'), label2)

    return sliceim
