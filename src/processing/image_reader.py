"""
Reads all image files from a given directory.
Supports common image formats: jpg, jpeg, png, bmp, tiff.
"""

import os

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def get_image_files(folder_path):
    """
    Scan a folder and return sorted list of image file paths.
    Only includes files with supported image extensions.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    image_files = []
    for filename in os.listdir(folder_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            image_files.append(os.path.join(folder_path, filename))

    image_files.sort()
    return image_files
