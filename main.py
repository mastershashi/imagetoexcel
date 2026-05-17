"""
Form to Excel - Desktop OCR Application

Reads handwritten school admission form images, extracts field data
using OpenCV alignment and EasyOCR, and exports to Excel with deduplication.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.app import FormToExcelApp


def main():
    app = FormToExcelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
