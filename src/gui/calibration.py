"""
Calibration window for marking field regions on a form image.

Uses tk.Label for image display (bulletproof on Windows/Mac) and
a transparent Canvas overlay for interactive rectangle drawing.
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2

from src.config.template_config import FIELD_NAMES, save_regions

REGION_COLORS = [
    "red", "blue", "green", "orange",
    "purple", "teal", "maroon", "navy",
    "olive", "magenta"
]


class CalibrationWindow(tk.Toplevel):

    def __init__(self, parent, aligned_image, current_regions):
        super().__init__(parent)
        self.title("Calibrate Field Regions - Draw rectangles around each field")
        self.configure(bg="white")

        self.aligned_image = aligned_image
        self.regions = dict(current_regions)
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.result = None
        self._photo = None

        img_rgb = cv2.cvtColor(self.aligned_image, cv2.COLOR_BGR2RGB)
        self._pil_original = Image.fromarray(img_rgb)

        scr_w = self.winfo_screenwidth() - 100
        scr_h = self.winfo_screenheight() - 150
        img_w, img_h = self._pil_original.size
        scale = min(scr_w / img_w, scr_h / img_h, 1.0)
        self._display_w = max(1, int(img_w * scale))
        self._display_h = max(1, int(img_h * scale))
        self._display_scale = scale

        win_w = self._display_w + 20
        win_h = self._display_h + 90
        self.geometry(f"{win_w}x{win_h}")
        self.resizable(False, False)

        self._build_ui()
        self._render()

    def _build_ui(self):
        top = tk.Frame(self, bg="#f0f0f0", padx=10, pady=6)
        top.pack(fill="x")

        tk.Label(top, text="Field:", bg="#f0f0f0",
                 font=("Arial", 11)).pack(side="left", padx=(5, 2))

        self.field_var = tk.StringVar(value=FIELD_NAMES[0])
        menu = tk.OptionMenu(top, self.field_var, *FIELD_NAMES)
        menu.config(width=15, font=("Arial", 10))
        menu.pack(side="left", padx=5)

        tk.Label(top, text="Select field, then drag rectangle on image.",
                 bg="#f0f0f0", fg="#555", font=("Arial", 10)).pack(side="left", padx=10)

        tk.Button(top, text="  Save & Close  ", command=self._save,
                  bg="#00b894", fg="white", font=("Arial", 11, "bold"),
                  relief="raised", cursor="hand2").pack(side="right", padx=5)

        container = tk.Frame(self, bg="white")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        self.image_label = tk.Label(container, bg="white", anchor="nw")
        self.image_label.pack()

        self.image_label.bind("<ButtonPress-1>", self._on_mouse_down)
        self.image_label.bind("<B1-Motion>", self._on_mouse_drag)
        self.image_label.bind("<ButtonRelease-1>", self._on_mouse_up)

        bottom = tk.Frame(self, bg="#f0f0f0", padx=10, pady=4)
        bottom.pack(fill="x")
        self.status = tk.Label(bottom, text="Select a field, then draw a rectangle on the image.",
                               bg="#f0f0f0", fg="#333", font=("Arial", 10), anchor="w")
        self.status.pack(fill="x")

    def _render(self):
        """Render the form image with region overlays into a single image on the Label."""
        composite = self._pil_original.resize(
            (self._display_w, self._display_h), Image.LANCZOS
        ).copy()

        draw = ImageDraw.Draw(composite)
        s = self._display_scale

        for i, field_name in enumerate(FIELD_NAMES):
            if field_name in self.regions:
                r = self.regions[field_name]
                x1 = int(r["x"] * s)
                y1 = int(r["y"] * s)
                x2 = int((r["x"] + r["w"]) * s)
                y2 = int((r["y"] + r["h"]) * s)
                color = REGION_COLORS[i % len(REGION_COLORS)]

                for offset in range(3):
                    draw.rectangle(
                        [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
                        outline=color
                    )

                label_y = max(0, y1 - 14)
                draw.rectangle([x1, label_y, x1 + len(field_name) * 7 + 6, label_y + 14],
                               fill=color)
                draw.text((x1 + 3, label_y + 1), field_name, fill="white")

        if hasattr(self, '_drag_rect'):
            dr = self._drag_rect
            for offset in range(2):
                draw.rectangle(
                    [dr[0] - offset, dr[1] - offset, dr[2] + offset, dr[3] + offset],
                    outline="lime"
                )

        self._photo = ImageTk.PhotoImage(composite)
        self.image_label.configure(image=self._photo)

    def _on_mouse_down(self, event):
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        if hasattr(self, '_drag_rect'):
            del self._drag_rect

    def _on_mouse_drag(self, event):
        if not self.drawing:
            return
        self._drag_rect = (
            min(self.start_x, event.x), min(self.start_y, event.y),
            max(self.start_x, event.x), max(self.start_y, event.y)
        )
        self._render()

    def _on_mouse_up(self, event):
        if not self.drawing:
            return
        self.drawing = False

        if hasattr(self, '_drag_rect'):
            del self._drag_rect

        s = self._display_scale
        x1 = int(min(self.start_x, event.x) / s)
        y1 = int(min(self.start_y, event.y) / s)
        x2 = int(max(self.start_x, event.x) / s)
        y2 = int(max(self.start_y, event.y) / s)

        x1 = max(0, x1)
        y1 = max(0, y1)
        w = max(10, x2 - x1)
        h = max(10, y2 - y1)

        field_name = self.field_var.get()
        self.regions[field_name] = {"x": x1, "y": y1, "w": w, "h": h}

        self._render()

        idx = FIELD_NAMES.index(field_name)
        if idx + 1 < len(FIELD_NAMES):
            next_field = FIELD_NAMES[idx + 1]
            self.field_var.set(next_field)
            self.status.configure(text=f"Saved {field_name}. Now draw: {next_field}")
        else:
            self.status.configure(text=f"All fields mapped! Click 'Save & Close'.")

    def _save(self):
        self.result = self.regions
        save_regions(self.regions)
        self.destroy()
