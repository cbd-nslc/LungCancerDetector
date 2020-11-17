import hashlib
import os
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Union, List

sys.path.append("..")
sys.path.append('../DSB2017')

from DSB2017.utils import directory_padding


class UploadType(Enum):
    MHD_RAW = 'mhd_raw'
    DICOM = 'dicom'
    IMAGES = 'images'
    INVALID = 'invalid'


class AllowedCompressedExtensions(Enum):
    _zip = '.zip'
    _7z = '.7z'


ALLOWED_COMPRESSED_EXTENSIONS = [ext.value for ext in AllowedCompressedExtensions]


class UploadError(Enum):
    ERROR_100 = f'Raise UI warning, if single file, it must be a compressed archive of image files, in {str(ALLOWED_COMPRESSED_EXTENSIONS)}'
    ERROR_101 = 'Raise UI Warning, user should upload RAW and MHD file with the same filename'
    ERROR_102 = 'Raise UI warning, user should upload multiple image file with the same extension'


def handle_file_list(file_paths: list):
    if len(file_paths) == 1:
        file_ext = os.path.splitext(file_paths[0])[1].lower()
        if file_ext not in ALLOWED_COMPRESSED_EXTENSIONS:
            return UploadError.ERROR_100, None

        else:
            return handle_file_list(handle_compressed_file(file_paths[0]))
    else:
        # Multiple file upload
        file_ext_list = [os.path.splitext(filepath)[1].lower() for filepath in file_paths]
        unique_file_ext = tuple(set(file_ext_list))
        if len(unique_file_ext) > 1:
            if '.raw' in unique_file_ext and '.mhd' in unique_file_ext:
                file_names = set([os.path.splitext(os.path.basename(filepath))[0] for filepath in file_paths])
                if len(file_names) == 1:
                    return UploadType.MHD_RAW, list(filter(lambda str: True if '.mhd' in str else False, file_paths))[0]
                else:
                    return UploadError.ERROR_101, None
            else:
                return UploadError.ERROR_102, None

        else:
            # Multiple file, same extension
            file_ext = os.path.splitext(file_paths[0])[1]
            # DICOM Files handling
            if file_ext == '.dcm':
                return UploadType.DICOM, dicom_files_handling(file_paths)


def dicom_files_handling(dicom_files: list):
    parent_dir = str(Path(dicom_files[0]).parent)
    return directory_padding(parent_dir)


def handle_compressed_file(file_path: str):
    file_ext = os.path.splitext(file_path)[1].lower()
    file_name = os.path.splitext(file_path)[0]
    parent_dir = Path(file_path).parent

    extract_dir = os.path.join(parent_dir, file_name)
    if not os.path.isdir(extract_dir):
        os.makedirs(extract_dir)

    if file_ext == AllowedCompressedExtensions._zip.value:
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    elif file_ext == AllowedCompressedExtensions._7z.value:
        from pyunpack import Archive
        Archive(file_path).extractall(extract_dir)

    file_list = []
    for path, subdirs, files in os.walk(extract_dir):
        for name in files:
            file_list.append(os.path.join(path, name))
    return file_list


def md5_checksum(file_path: Union[List[str], str]):
    if isinstance(file_path, list):
        hash_obj = hashlib.md5(open(file_path[0], 'rb').read())
        for fname in file_path[1:]:
            hash_obj.update(open(fname, 'rb').read())
        checksum = hash_obj.hexdigest()
        return checksum
    elif isinstance(file_path, str):
        return md5_checksum([file_path])
    else:
        raise UserWarning(f'Input type not supported: {type(file_path)}')


def get_relative_path(full_path, common_save_dir):
    return str(Path(full_path).relative_to(common_save_dir))


def get_full_path(relative_path, common_save_dir):
    return str(os.path.join(common_save_dir, relative_path))


def move_files(new_path: str, file_paths: list):
    base_names = [os.path.basename(f) for f in file_paths]
    new_file_paths = [os.path.join(new_path, basename) for basename in base_names]
    assert len(file_paths) == len(new_file_paths)
    for i in range(len(file_paths)):
        shutil.move(file_paths[i], new_file_paths[i])
    return new_file_paths
