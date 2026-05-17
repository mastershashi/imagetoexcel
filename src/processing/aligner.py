"""
OpenCV-based form alignment.

Detects the form boundary (largest rectangle) in a photographed image
and applies a perspective warp to produce a standardized, flat image.
"""

import cv2
import numpy as np
from src.config.template_config import STANDARD_WIDTH, STANDARD_HEIGHT


def order_points(pts):
    """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def find_form_contour(image):
    """
    Find the largest rectangular contour in the image (the form boundary).
    Returns the 4 corner points or None if not found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 200)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=2)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours[:10]:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2)

    return None


def align_form(image, target_width=STANDARD_WIDTH, target_height=STANDARD_HEIGHT):
    """
    Detect the form in the image and warp it to a standard rectangle.

    Returns:
        aligned_image: The perspective-corrected image, or None on failure.
        success: Boolean indicating if alignment was successful.
    """
    corners = find_form_contour(image)

    if corners is None:
        h, w = image.shape[:2]
        aspect = w / h
        if aspect > (target_width / target_height):
            new_w = target_width
            new_h = int(target_width / aspect)
        else:
            new_h = target_height
            new_w = int(target_height * aspect)
        resized = cv2.resize(image, (new_w, new_h))
        padded = np.zeros((target_height, target_width, 3), dtype=np.uint8) + 255
        y_off = (target_height - new_h) // 2
        x_off = (target_width - new_w) // 2
        padded[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return padded, False

    ordered = order_points(corners.astype("float32"))
    dst = np.array([
        [0, 0],
        [target_width - 1, 0],
        [target_width - 1, target_height - 1],
        [0, target_height - 1]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(image, matrix, (target_width, target_height))
    return warped, True


def load_and_align(image_path, target_width=STANDARD_WIDTH, target_height=STANDARD_HEIGHT):
    """Load an image from disk and align it."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    return align_form(image, target_width, target_height)
