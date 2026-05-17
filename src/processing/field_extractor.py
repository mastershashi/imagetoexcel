"""
Extracts individual field regions from an aligned form image
based on template configuration coordinates.
"""

import cv2
import numpy as np


def preprocess_field(field_image):
    """
    Preprocess a cropped field image for better OCR accuracy.
    Applies grayscale conversion, thresholding, and noise removal.
    """
    if len(field_image.shape) == 3:
        gray = cv2.cvtColor(field_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = field_image.copy()

    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 8
    )

    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return binary


def extract_fields(aligned_image, field_regions):
    """
    Crop each field from the aligned image using region coordinates.

    Args:
        aligned_image: The perspective-corrected form image.
        field_regions: Dict of field_name -> {x, y, w, h}.

    Returns:
        Dict of field_name -> preprocessed cropped image.
    """
    fields = {}
    h, w = aligned_image.shape[:2]

    for field_name, region in field_regions.items():
        x = max(0, region["x"])
        y = max(0, region["y"])
        x2 = min(w, x + region["w"])
        y2 = min(h, y + region["h"])

        if x2 <= x or y2 <= y:
            continue

        cropped = aligned_image[y:y2, x:x2]

        if cropped.size == 0:
            continue

        processed = preprocess_field(cropped)
        fields[field_name] = processed

    return fields


def extract_fields_raw(aligned_image, field_regions):
    """
    Same as extract_fields but returns unprocessed crops (for display/preview).
    """
    fields = {}
    h, w = aligned_image.shape[:2]

    for field_name, region in field_regions.items():
        x = max(0, region["x"])
        y = max(0, region["y"])
        x2 = min(w, x + region["w"])
        y2 = min(h, y + region["h"])

        if x2 <= x or y2 <= y:
            continue

        cropped = aligned_image[y:y2, x:x2]
        if cropped.size > 0:
            fields[field_name] = cropped

    return fields
