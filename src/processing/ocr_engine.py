"""
EasyOCR wrapper for extracting text from preprocessed field images.
Handles initialization, caching the reader, and post-processing results.
"""

import re
import easyocr
import numpy as np

_reader = None


def get_reader(languages=None):
    """Lazy-initialize and cache the EasyOCR reader."""
    global _reader
    if _reader is None:
        langs = languages or ["en"]
        _reader = easyocr.Reader(langs, gpu=False)
    return _reader


def ocr_field(field_image, reader=None):
    """
    Run OCR on a single preprocessed field image.

    Returns the extracted text string (cleaned).
    """
    if reader is None:
        reader = get_reader()

    if isinstance(field_image, np.ndarray) and len(field_image.shape) == 2:
        img = field_image
    else:
        img = field_image

    results = reader.readtext(img, detail=0, paragraph=True)

    if not results:
        return ""

    text = " ".join(results)
    return clean_text(text)


def clean_text(text):
    """Basic text cleanup for OCR output."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('|', '')
    text = text.replace('\\', '')
    return text


def ocr_all_fields(field_images, reader=None):
    """
    Run OCR on all field images.

    Args:
        field_images: Dict of field_name -> preprocessed image.

    Returns:
        Dict of field_name -> extracted text.
    """
    if reader is None:
        reader = get_reader()

    results = {}
    for field_name, img in field_images.items():
        results[field_name] = ocr_field(img, reader)

    return results
