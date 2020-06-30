import os

WORKER_POOL_SIZE = 8

TARGET_VOXEL_MM = 1.00
MEAN_PIXEL_VALUE_NODULE = 41
LUNA_SUBSET_START_INDEX = 0
SEGMENTER_IMG_SIZE = 320


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = "/home/vantuan5644/PycharmProjects/dataset/"
EXTRA_DATA_DIR = PROJECT_ROOT + "resources/"

NDSB3_RAW_SRC_DIR = BASE_DIR + "dataset_ndsb/train/"
LUNA16_RAW_SRC_DIR = BASE_DIR + "dataset_luna/train/"

NDSB3_EXTRACTED_IMAGE_DIR = BASE_DIR + "ndsb3_extracted_images/"
LUNA16_EXTRACTED_IMAGE_DIR = BASE_DIR + "luna16_extracted_images/"
NDSB3_NODULE_DETECTION_DIR = BASE_DIR + "ndsb3_nodule_predictions/"
