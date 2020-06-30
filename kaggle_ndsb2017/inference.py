import glob
import math
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from pathlib import Path

import cv2
import numpy
import sys
# sys.path.append('.')

from kaggle_ndsb2017 import helpers
from kaggle_ndsb2017 import settings
from kaggle_ndsb2017 import step2_train_nodule_detector
from kaggle_ndsb2017.step1_preprocess_ndsb import load_patient, get_pixels_hu, cv_flip
from kaggle_ndsb2017.step2_train_nodule_detector import CUBE_SIZE
from kaggle_ndsb2017.step3_predict_nodules import PREDICT_STEP, prepare_image_for_net3D, P_TH


def extract_dicom_images_patient(src_dir, target_dir=None, write_to_imgs=True):
    print("Source dicom dir: ", src_dir)
    id = os.path.basename(os.path.abspath(src_dir))

    if write_to_imgs:
        if target_dir is None:
            target_dir = os.path.join(Path(src_dir).parent, id + '_extracted')
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        print("Target dicom dir: ", target_dir)

    slices = load_patient(src_dir)
    print(
        f"Len slides: {len(slices)} \t Slide thickness: {slices[0].SliceThickness} \t Pixel Spacing: {slices[0].PixelSpacing}")
    print("Orientation: ", slices[0].ImageOrientationPatient)
    # assert slices[0].ImageOrientationPatient == [1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000]
    cos_value = (slices[0].ImageOrientationPatient[0])
    cos_degree = round(math.degrees(math.acos(cos_value)), 2)

    pixels = get_pixels_hu(slices)
    image = pixels
    print("Img shape:", image.shape)

    invert_order = slices[1].ImagePositionPatient[2] > slices[0].ImagePositionPatient[2]
    print("Invert order: ", invert_order, " - ", slices[1].ImagePositionPatient[2], ",",
          slices[0].ImagePositionPatient[2])

    pixel_spacing = slices[0].PixelSpacing
    pixel_spacing.append(slices[0].SliceThickness)
    image = helpers.rescale_patient_images(image, pixel_spacing, settings.TARGET_VOXEL_MM)
    if not invert_order:
        image = numpy.flipud(image)


    full_img = []
    full_mask = []

    for i in range(image.shape[0]):
        org_img = image[i]
        # if there exists slope,rotation image with corresponding degree
        if cos_degree > 0.0:
            org_img = cv_flip(org_img, org_img.shape[1], org_img.shape[0], cos_degree)
        img, mask = helpers.get_segmented_lungs(org_img.copy())
        org_img = helpers.normalize_hu(org_img)
        org_img = org_img * 255
        mask = mask * 255
        if write_to_imgs:
            file_name = "img_" + str(i).rjust(4, '0') + "_i.png"
            img_path = os.path.join(target_dir, file_name)
            cv2.imwrite(img_path, org_img)
            cv2.imwrite(img_path.replace("_i.png", "_m.png"), mask * 255)
        else:
            full_img.append(org_img.reshape((1,) + org_img.shape))
            full_mask.append(mask.reshape((1,) + mask.shape))

    return target_dir if write_to_imgs else (numpy.vstack(full_img), numpy.vstack(full_mask))



def load_patient_images(extracted_dir, wildcard="*.*", exclude_wildcards: list = None):
    if exclude_wildcards is None:
        exclude_wildcards = []
    src_img_paths = glob.glob(os.path.join(extracted_dir, wildcard))
    for exclude_wildcard in exclude_wildcards:
        exclude_img_paths = glob.glob(extracted_dir + exclude_wildcard)
        src_img_paths = [im for im in src_img_paths if im not in exclude_img_paths]
    src_img_paths.sort()
    images = [cv2.imread(img_path, cv2.IMREAD_GRAYSCALE) for img_path in src_img_paths]
    images = [im.reshape((1,) + im.shape) for im in images]
    res = numpy.vstack(images)
    return res


def inference(src_dir, pretrained_weight, target_dir=None, extract_dicom=False, flip=False, magnification=1, ext_name=""):
    id = os.path.basename(os.path.abspath(src_dir))

    if target_dir is None:
        target_dir = os.path.join(Path(src_dir).parent, id + '_extracted')

    flip_ext = ""
    if flip:
        flip_ext = "_flip"

    suffix = "predictions" + str(int(magnification * 10)) + flip_ext + "_" + ext_name
    target_dir += os.path.join(target_dir, suffix)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    sw = helpers.Stopwatch.start_new()
    model = step2_train_nodule_detector.get_net(input_shape=(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE, 1),
                                                load_weight_path=pretrained_weight)
    print("Preprocessing dicom files")
    if extract_dicom:
        # Extract dcm files to png
        extracted_dir = extract_dicom_images_patient(src_dir=src_dir, write_to_imgs=True)
        patient_img = load_patient_images(extracted_dir, "*_i.png")
        patient_mask = load_patient_images(extracted_dir, "*_m.png")
    else:
        patient_img, patient_mask = extract_dicom_images_patient(src_dir, write_to_imgs=False)

    print("Preprocess mhd files successfully")

    if magnification != 1:
        patient_img = helpers.rescale_patient_images(patient_img, (1, 1, 1), magnification)
    if magnification != 1:
        patient_mask = helpers.rescale_patient_images(patient_mask, (1, 1, 1), magnification, is_mask_image=True)

    step = PREDICT_STEP
    CROP_SIZE = CUBE_SIZE

    predict_volume_shape_list = [0, 0, 0]
    for dim in range(3):
        dim_indent = 0
        while dim_indent + CROP_SIZE < patient_img.shape[dim]:
            predict_volume_shape_list[dim] += 1
            dim_indent += step

    predict_volume_shape = (predict_volume_shape_list[0], predict_volume_shape_list[1], predict_volume_shape_list[2])
    predict_volume = numpy.zeros(shape=predict_volume_shape, dtype=float)
    print("Predict volume shape: ", predict_volume.shape)

    for z in range(0, predict_volume_shape[0]):
        for y in range(0, predict_volume_shape[1]):
            for x in range(0, predict_volume_shape[2]):
                # if cube_img is None:
                cube_img = patient_img[z * step:z * step + CROP_SIZE, y * step:y * step + CROP_SIZE,
                           x * step:x * step + CROP_SIZE]
                cube_mask = patient_mask[z * step:z * step + CROP_SIZE, y * step:y * step + CROP_SIZE,
                            x * step:x * step + CROP_SIZE]

                if cube_mask.sum() < 2000:
                    pass
                else:
                    if flip:
                        cube_img = cube_img[:, :, ::-1]

                    if CROP_SIZE != CUBE_SIZE:
                        cube_img = helpers.rescale_patient_images2(cube_img, (CUBE_SIZE, CUBE_SIZE, CUBE_SIZE))

                    img_prep = prepare_image_for_net3D(cube_img)
                    # batch_list.append(img_prep)
                    # batch_list_coords.append((z, y, x))
                    # if len(batch_list) % batch_size == 0:
                    #     batch_data = numpy.vstack(batch_list)
                    p = model.predict(img_prep)
                    p_z = z
                    p_y = y
                    p_x = x
                    nodule_chance = float(p[0][0])
                    predict_volume[p_z, p_y, p_x] = nodule_chance
                    if nodule_chance > P_TH:
                        p_z = p_z * step + CROP_SIZE / 2
                        p_y = p_y * step + CROP_SIZE / 2
                        p_x = p_x * step + CROP_SIZE / 2

                        p_z_perc = round(p_z / patient_img.shape[0], 4)
                        p_y_perc = round(p_y / patient_img.shape[1], 4)
                        p_x_perc = round(p_x / patient_img.shape[2], 4)
                        diameter_mm = round(float(p[1][0]), 4)
                        # diameter_perc = round(2 * step / patient_img.shape[2], 4)
                        diameter_perc = round(2 * step / patient_img.shape[2], 4)
                        diameter_perc = round(diameter_mm / patient_img.shape[2], 4)
                        nodule_chance = round(nodule_chance, 4)
                        results = {'coord_x': p_x_perc, 'coord_y': p_y_perc, 'coord_z': p_z_perc,
                                   'diameter': diameter_perc, 'diameter_mm': diameter_mm,
                                   'nodule_chance': nodule_chance}
                        print(results)
    print("Done in: ", sw.get_elapsed_seconds(), "seconds")


if __name__ == "__main__":
    test_dir = "/home/vantuan5644/PycharmProjects/dataset/dataset_ndsb/test/0a0c32c9e08cc2ea76a71649de56be6d"
    # extract_dicom_images_patient(test_dir)
    inference(test_dir, pretrained_weight="trained_models/model_luna_posnegndsb_v2__fs_h1_end.hd5", ext_name="luna_posnegndsb_v")