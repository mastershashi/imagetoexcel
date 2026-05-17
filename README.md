# Form to Excel - OCR Desktop Tool

A desktop application that extracts handwritten school admission form data from images and exports it to Excel. Uses OpenCV for image alignment and EasyOCR for text recognition -- fully offline, no API keys needed.

## Features

- **Batch Processing**: Select a folder of form images and process them all at once
- **OpenCV Alignment**: Automatically detects form boundaries and corrects perspective
- **EasyOCR**: Deep learning based OCR that handles handwritten text
- **Template Calibration**: One-time setup to mark field positions on your form template
- **Deduplication**: Prevents duplicate entries using fuzzy name matching + roll number + class
- **Excel Export**: Professional styled Excel output with auto-filter

## Setup

### Prerequisites

- Python 3.9 or higher

### Install Dependencies

```bash
cd Imagetoexcel
pip install -r requirements.txt
```

> **Note**: On first run, EasyOCR will download its text detection model (~100MB). This only happens once.

## Usage

### 1. Launch the App

```bash
python main.py
```

### 2. Calibrate (One-Time Setup)

1. Click **Select Image Folder** and pick a folder with your form images
2. Click **Calibrate Template**
3. A calibration window opens showing the first form image
4. For each field (student_name, mother_name, roll_no, etc.), select it from the dropdown and draw a rectangle around that field on the image
5. Click **Save & Close** when done

The calibration is saved and reused for all future forms with the same template.

### 3. Process Forms

1. Select your **Image Folder** (containing scanned/photographed forms)
2. Select an **Output Excel** file path
3. Click **Process All Images**
4. Watch progress in the log and preview table
5. The Excel file is saved automatically when done

### 4. Re-running

If you add more forms to the folder and re-run, only new (non-duplicate) records are appended to the existing Excel file.

## Supported Image Formats

JPG, JPEG, PNG, BMP, TIFF, WebP

## Project Structure

```
Imagetoexcel/
  main.py                      # App entry point
  requirements.txt             # Python dependencies
  README.md                    # This file
  src/
    config/
      template_config.py       # Field region coordinates and mapping
      field_regions.json       # Saved calibration data (auto-generated)
    processing/
      image_reader.py          # Scans folder for image files
      aligner.py               # OpenCV form detection + perspective warp
      field_extractor.py       # Crops field regions from aligned image
      ocr_engine.py            # EasyOCR text extraction
    export/
      excel_writer.py          # Excel generation with deduplication
    gui/
      app.py                   # CustomTkinter GUI
```

## Tips for Best Results

- **Photo Quality**: Take clear, well-lit photos. Avoid shadows and glare.
- **Form Alignment**: Try to photograph the form straight-on. The app corrects perspective, but cleaner input = better results.
- **Capital Letters**: The forms should be filled in capital letters (as printed on the form) for best OCR accuracy.
- **Calibration**: Spend time on calibration -- accurate field regions dramatically improve extraction quality.

## Packaging for Windows (.exe)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "FormToExcel" main.py
```

The executable will be in the `dist/` folder.
