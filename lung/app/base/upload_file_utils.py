import os
from enum import Enum
from pathlib import Path


class UploadType(Enum):
    MHD_RAW = 'mhd_raw'
    DICOM = 'dicom'
    IMAGES = 'images'
    INVALID = 'invalid'


class CompressedFileExtensions(Enum):
    _rar = '.rar'
    _zip = '.zip'
    _7z = '.7z'


COMPRESSED_FILE_EXTENSIONS = [ext.value for ext in CompressedFileExtensions]


def handle_file_list(file_paths: list):
    if len(file_paths) == 1:
        file_ext = os.path.splitext(file_paths[0])[1].lower()
        if file_ext not in COMPRESSED_FILE_EXTENSIONS:
            # TODO: Raise UI warning, if single file, it must be a compressed archive of image files
            pass
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
                    # TODO: Raise UI Warning, user should upload RAW and MHD file with the same filename
                    return UploadType.INVALID, None
            else:
                # TODO: Raise UI warning, user should upload multiple image file with the same extension
                return UploadType.INVALID, None

        else:
            # Multiple file, same extension
            file_ext = os.path.splitext(file_paths[0])[1]
            # DICOM Files handling
            if file_ext == '.dcm':
                return UploadType.DICOM, dicom_files_handling(file_paths)


def dicom_files_handling(dicom_files):
    parent_dir = Path(dicom_files[0]).parent
    return parent_dir


def handle_compressed_file(file_path: str):
    file_ext = os.path.splitext(file_path[0])[1].lower()
    if file_ext == CompressedFileExtensions._zip.value:
        return []
