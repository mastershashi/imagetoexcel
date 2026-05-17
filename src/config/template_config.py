"""
Template configuration for form field regions.

Stores the pixel coordinates of each field on the aligned/warped form image.
The coordinates are relative to the standard output size after perspective warp.
Users calibrate these once using the GUI calibration tool.
"""

import json
import os

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "field_regions.json"
)

STANDARD_WIDTH = 1200
STANDARD_HEIGHT = 900

FIELD_NAMES = [
    "student_name",
    "father_name",
    "mother_name",
    "class",
    "roll_no",
    "section",
    "house",
    "address",
    "date_of_birth",
    "photo_no",
]

EXCEL_COLUMNS = [
    "Name",
    "Father Name",
    "Mother Name",
    "Class",
    "Roll No",
    "Sec",
    "Address",
    "Date of Birth",
]

FIELD_TO_EXCEL = {
    "student_name": "Name",
    "father_name": "Father Name",
    "mother_name": "Mother Name",
    "class": "Class",
    "roll_no": "Roll No",
    "section": "Sec",
    "house": "House",
    "address": "Address",
    "date_of_birth": "Date of Birth",
    "photo_no": "Photo No",
}


def get_default_regions():
    """
    Returns default field regions estimated from the sample form layout.
    Each region is (x, y, width, height) in pixels on the standardized image.
    These should be recalibrated by the user via the GUI calibration tool.
    """
    return {
        "student_name":   {"x": 280, "y": 80,  "w": 700, "h": 60},
        "father_name":    {"x": 280, "y": 200, "w": 700, "h": 60},
        "mother_name":    {"x": 280, "y": 260, "w": 700, "h": 60},
        "class":          {"x": 280, "y": 140, "w": 200, "h": 50},
        "roll_no":        {"x": 520, "y": 140, "w": 150, "h": 50},
        "section":        {"x": 280, "y": 140, "w": 100, "h": 50},
        "house":          {"x": 700, "y": 140, "w": 200, "h": 50},
        "address":        {"x": 280, "y": 320, "w": 700, "h": 60},
        "date_of_birth":  {"x": 280, "y": 380, "w": 400, "h": 60},
        "photo_no":       {"x": 900, "y": 80,  "w": 200, "h": 60},
    }


def load_regions(config_path=None):
    path = config_path or DEFAULT_CONFIG_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return get_default_regions()


def save_regions(regions, config_path=None):
    path = config_path or DEFAULT_CONFIG_PATH
    with open(path, "w") as f:
        json.dump(regions, f, indent=2)
