# Form To Excel - Installation Guide

Two ways to install: **Method A** (one-click batch file) or **Method B** (professional NSIS installer `.exe`). Both do the same thing automatically.

---

## Method A: One-Click Batch Installer (Easiest)

No extra tools needed. Just double-click.

### Steps

1. Copy the entire `Imagetoexcel` project folder to the Windows machine

2. Open the `installer` folder inside the project

3. **Right-click `install.bat`** and select **"Run as administrator"**

4. The installer will:

   | Step | What happens | Time |
   |------|-------------|------|
   | 1/7 | Check if Python 3.9+ is installed | 2 sec |
   | 2/7 | Copy application files to install directory | 2 sec |
   | 3/7 | Create Python virtual environment | 5 sec |
   | 4/7 | Download and install all packages (~800 MB) | 5-15 min |
   | 5/7 | Download OCR model (~100 MB) | 1-3 min |
   | 6/7 | Create Desktop and Start Menu shortcuts | 2 sec |
   | 7/7 | Done! Option to launch the app | - |

5. If Python is not found, the installer **downloads and installs Python 3.11 automatically**

6. When finished, you'll see:
   - **Desktop shortcut**: "Form To Excel"
   - **Start Menu entry**: "Form To Excel"
   - **Uninstaller**: inside the install directory

### Default Install Location

```
C:\Users\<YourName>\AppData\Local\FormToExcel\
```

You can change this when prompted during installation.

---

## Method B: Professional NSIS Installer (.exe)

Creates a single `FormToExcel_Setup.exe` that looks and behaves like a standard Windows installer (with wizard pages, progress bar, Add/Remove Programs entry).

### Prerequisites

Install **NSIS** (Nullsoft Scriptable Install System):
- Download: https://nsis.sourceforge.io/Download
- Install it (default settings are fine)

### Build the Installer

1. Open **Command Prompt** in the project root:

```bash
cd C:\path\to\Imagetoexcel
```

2. Create the `dist` folder:

```bash
mkdir dist
```

3. Compile the NSIS script:

```bash
makensis installer\installer.nsi
```

4. The installer is created at:

```
dist\FormToExcel_Setup.exe
```

### Distribute

Send `FormToExcel_Setup.exe` to anyone. When they run it:
1. Welcome screen appears
2. They choose install location
3. Everything installs automatically (Python, packages, model)
4. Finish screen with "Launch" checkbox
5. App appears in Windows **Add/Remove Programs** for clean uninstall

---

## What Gets Installed

```
FormToExcel\
  main.py                    # App entry point
  requirements.txt           # Dependencies list
  FormToExcel.bat            # App launcher
  FormToExcel.vbs            # Silent launcher (no cmd window)
  Uninstall.bat              # Uninstaller
  venv\                      # Python virtual environment (~1.5 GB)
    Scripts\python.exe
    Lib\site-packages\       # All packages (EasyOCR, OpenCV, etc.)
  src\                       # Application source code
    config\
    processing\
    export\
    gui\
  installer\                 # Installer scripts (can be deleted after install)
```

Total disk space after installation: **~2 GB** (mostly PyTorch + EasyOCR model).

---

## Running the App After Installation

Three ways to launch:

1. **Desktop shortcut**: Double-click "Form To Excel" on desktop
2. **Start Menu**: Search "Form To Excel" in Windows Start
3. **Command line**:
   ```bash
   cd C:\Users\<YourName>\AppData\Local\FormToExcel
   FormToExcel.bat
   ```

---

## Uninstalling

### If installed via Method A (batch):
- Run `Uninstall.bat` inside the install directory
- Or manually delete the install folder + shortcuts

### If installed via Method B (NSIS):
- Go to **Windows Settings > Apps > Apps & features**
- Find "Form To Excel" and click **Uninstall**
- Or run `Uninstall.exe` inside the install directory

---

## Troubleshooting

### "PowerShell script cannot be loaded" error
Right-click `install.bat` and select **Run as administrator**. The script sets `-ExecutionPolicy Bypass` automatically.

### Python download fails
Install Python 3.11 manually from https://www.python.org/downloads/ -- make sure to check **"Add Python to PATH"** during installation. Then re-run `install.bat`.

### Installation hangs at "Installing dependencies"
This step downloads ~800 MB of packages. On slow connections it can take 15+ minutes. Check your internet connection and wait.

### App window doesn't appear
Run from command line to see errors:
```bash
cd C:\Users\<YourName>\AppData\Local\FormToExcel
venv\Scripts\activate
python main.py
```

### "torch" or "easyocr" import errors
The CPU-only PyTorch may need reinstalling:
```bash
cd C:\Users\<YourName>\AppData\Local\FormToExcel
venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install easyocr
```

### Want to reduce disk space (~2 GB is too much)
Most space is PyTorch. The CPU-only version is already used (~200 MB vs ~800 MB for GPU). This is the minimum for EasyOCR to work.

---

## Offline Installation (No Internet on Target Machine)

If the target Windows machine has no internet:

1. On a machine WITH internet, install everything normally
2. Copy the entire install directory (`FormToExcel\` with `venv\`) to a USB drive
3. Copy to the target machine
4. Manually create shortcuts (or run the batch launcher directly)

The venv is self-contained and portable between same-architecture Windows machines.
