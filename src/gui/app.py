"""
Main GUI application using CustomTkinter.

Provides:
- Folder selection for input images
- Output Excel file selection
- Calibration mode to define field regions on a sample form
- Process button with progress tracking
- Data preview table
- Status log
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import numpy as np

from src.config.template_config import (
    load_regions, save_regions, FIELD_NAMES,
    FIELD_TO_EXCEL, STANDARD_WIDTH, STANDARD_HEIGHT,
)
from src.processing.image_reader import get_image_files
from src.processing.aligner import load_and_align
from src.processing.field_extractor import extract_fields
from src.processing.ocr_engine import get_reader, ocr_all_fields
from src.export.excel_writer import export_to_excel
from src.gui.calibration import CalibrationWindow


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FormToExcelApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Form to Excel - OCR Tool")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.image_folder = ""
        self.excel_path = ""
        self.field_regions = load_regions()
        self.processing = False
        self.all_extracted_data = []

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="Form to Excel",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=15)
        ctk.CTkLabel(
            header,
            text="Extract handwritten form data to Excel using OCR",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(pady=(0, 10))

        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=20, pady=10)

        row1 = ctk.CTkFrame(controls, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkButton(
            row1, text="Select Image Folder", width=180,
            command=self._select_folder
        ).pack(side="left", padx=5)
        self.folder_label = ctk.CTkLabel(row1, text="No folder selected", text_color="gray")
        self.folder_label.pack(side="left", padx=10)

        row2 = ctk.CTkFrame(controls, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkButton(
            row2, text="Select Output Excel", width=180,
            command=self._select_excel
        ).pack(side="left", padx=5)
        self.excel_label = ctk.CTkLabel(row2, text="No output file selected", text_color="gray")
        self.excel_label.pack(side="left", padx=10)

        row3 = ctk.CTkFrame(controls, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        ctk.CTkButton(
            row3, text="Calibrate Template", width=180,
            fg_color="#6c5ce7", hover_color="#5a4bd1",
            command=self._calibrate
        ).pack(side="left", padx=5)
        self.calibrate_label = ctk.CTkLabel(
            row3,
            text="Define field positions on a sample form (one-time setup)",
            text_color="gray"
        )
        self.calibrate_label.pack(side="left", padx=10)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=5)

        self.process_btn = ctk.CTkButton(
            action_frame, text="Process All Images", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#00b894", hover_color="#00a381",
            command=self._process
        )
        self.process_btn.pack(fill="x", padx=5)

        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=5)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=5)
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready", text_color="gray")
        self.progress_label.pack(pady=2)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        ctk.CTkLabel(
            table_frame, text="Extracted Data Preview",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        tree_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("Name", "Father Name", "Mother Name", "Class",
                   "Roll No", "Sec", "Address", "DOB", "Photo No")
        self.tree = tk.ttk.Treeview(tree_container, columns=columns, show="headings", height=8)

        style = tk.ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white",
                        fieldbackground="#2b2b2b", rowheight=28)
        style.configure("Treeview.Heading", background="#1a1a2e", foreground="white",
                        font=("Calibri", 10, "bold"))
        style.map("Treeview", background=[("selected", "#3d5a80")])

        col_widths = {"Name": 120, "Father Name": 110, "Mother Name": 110,
                      "Class": 55, "Roll No": 55, "Sec": 35,
                      "Address": 130, "DOB": 80, "Photo No": 60}

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor="center")

        scrollbar = tk.ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.log_text = ctk.CTkTextbox(log_frame, height=100)
        self.log_text.pack(fill="x", padx=5, pady=5)

    def _log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing form images")
        if folder:
            self.image_folder = folder
            try:
                files = get_image_files(folder)
                self.folder_label.configure(
                    text=f"{folder}  ({len(files)} images found)",
                    text_color="white"
                )
                self._log(f"Selected folder: {folder} ({len(files)} images)")
            except Exception as e:
                self.folder_label.configure(text=str(e), text_color="red")

    def _select_excel(self):
        path = filedialog.asksaveasfilename(
            title="Select output Excel file",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="student_data.xlsx"
        )
        if path:
            self.excel_path = path
            self.excel_label.configure(text=path, text_color="white")
            self._log(f"Output file: {path}")

    def _calibrate(self):
        if not self.image_folder:
            messagebox.showwarning("No Folder", "Please select an image folder first.")
            return

        files = get_image_files(self.image_folder)
        if not files:
            messagebox.showwarning("No Images", "No images found in the selected folder.")
            return

        self._log(f"Loading image for calibration: {files[0]}")
        try:
            aligned, success = load_and_align(files[0])
            self._log(f"Image loaded: {aligned.shape[1]}x{aligned.shape[0]}px. Form detected: {success}")
            if not success:
                self._log("Note: Form boundary not detected. Image was resized to standard dimensions.")

            cal_window = CalibrationWindow(self, aligned, self.field_regions)
            self.wait_window(cal_window)

            if cal_window.result:
                self.field_regions = cal_window.result
                self._log("Calibration saved! Field regions:")
                for name, r in cal_window.result.items():
                    self._log(f"  {name}: x={r['x']}, y={r['y']}, w={r['w']}, h={r['h']}")
                self.calibrate_label.configure(
                    text="Calibration complete",
                    text_color="#00b894"
                )
        except Exception as e:
            self._log(f"Calibration error: {e}")
            messagebox.showerror("Error", f"Failed to load image:\n{e}\n\nFile: {files[0]}")

    def _process(self):
        if self.processing:
            return

        if not self.image_folder:
            messagebox.showwarning("No Folder", "Please select an image folder first.")
            return
        if not self.excel_path:
            messagebox.showwarning("No Output", "Please select an output Excel file.")
            return

        self.processing = True
        self.process_btn.configure(state="disabled", text="Processing...")
        self.all_extracted_data = []

        for item in self.tree.get_children():
            self.tree.delete(item)

        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()

    def _process_worker(self):
        try:
            files = get_image_files(self.image_folder)
            total = len(files)
            if total == 0:
                self.after(0, lambda: self._log("No images found."))
                return

            self.after(0, lambda: self._log("Initializing OCR engine (first run downloads model ~100MB)..."))
            reader = get_reader()
            self.after(0, lambda: self._log("OCR engine ready.\n"))

            all_data = []

            for i, file_path in enumerate(files):
                filename = os.path.basename(file_path)
                self.after(0, lambda fn=filename, idx=i: self._log(f"[{idx+1}/{total}] Processing: {fn}"))

                progress = (i + 1) / total
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                self.after(0, lambda idx=i, t=total: self.progress_label.configure(
                    text=f"Processing image {idx+1} of {t}..."
                ))

                try:
                    aligned, success = load_and_align(file_path)
                    if not success:
                        self.after(0, lambda fn=filename: self._log(
                            f"  Warning: Form boundary not detected in {fn}"
                        ))

                    field_images = extract_fields(aligned, self.field_regions)
                    self.after(0, lambda n=len(field_images): self._log(
                        f"  Extracted {n} field regions"
                    ))

                    ocr_data = ocr_all_fields(field_images, reader)

                    for field_name, text in ocr_data.items():
                        self.after(0, lambda fn=field_name, t=text: self._log(
                            f"    {fn}: '{t}'"
                        ))

                    all_data.append(ocr_data)
                    self.after(0, lambda d=ocr_data: self._add_to_preview(d))

                except Exception as e:
                    self.after(0, lambda fn=filename, err=e: self._log(
                        f"  ERROR processing {fn}: {err}"
                    ))

            self.all_extracted_data = all_data
            self.after(0, lambda: self._log(f"\nOCR complete. Extracted data from {len(all_data)} forms."))
            self.after(0, lambda: self._log("Exporting to Excel..."))

            def on_export_progress(current, total_count, msg):
                self.after(0, lambda m=msg: self._log(f"  {m}"))

            added, skipped, total_rows = export_to_excel(
                all_data, self.excel_path, on_progress=on_export_progress
            )

            self.after(0, lambda: self._log(
                f"\nDone! Added: {added}, Skipped (duplicates): {skipped}, "
                f"Total records in file: {total_rows}"
            ))
            self.after(0, lambda: self.progress_label.configure(
                text=f"Complete - {added} added, {skipped} duplicates skipped"
            ))
            self.after(0, lambda: messagebox.showinfo(
                "Complete",
                f"Processing finished!\n\n"
                f"New records added: {added}\n"
                f"Duplicates skipped: {skipped}\n"
                f"Total records in file: {total_rows}\n\n"
                f"File saved to:\n{self.excel_path}"
            ))

        except Exception as e:
            self.after(0, lambda: self._log(f"\nFatal error: {e}"))
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, self._processing_done)

    def _add_to_preview(self, ocr_data):
        values = (
            ocr_data.get("student_name", ""),
            ocr_data.get("father_name", ""),
            ocr_data.get("mother_name", ""),
            ocr_data.get("class", ""),
            ocr_data.get("roll_no", ""),
            ocr_data.get("section", ""),
            ocr_data.get("address", ""),
            ocr_data.get("date_of_birth", ""),
            ocr_data.get("photo_no", ""),
        )
        self.tree.insert("", "end", values=values)

    def _processing_done(self):
        self.processing = False
        self.process_btn.configure(state="normal", text="Process All Images")
