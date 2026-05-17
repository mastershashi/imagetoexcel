# ============================================================================
#  Form To Excel - Professional Installer
#  Downloads Python, sets up environment, installs dependencies, creates
#  shortcuts, and launches the application.
# ============================================================================

param(
    [string]$InstallDir = "",
    [switch]$Silent = $false
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
$APP_NAME          = "Form To Excel"
$APP_EXE_NAME      = "FormToExcel"
$PYTHON_VERSION    = "3.11.9"
$PYTHON_INSTALLER  = "python-$PYTHON_VERSION-amd64.exe"
$PYTHON_URL        = "https://www.python.org/ftp/python/$PYTHON_VERSION/$PYTHON_INSTALLER"
$MIN_PYTHON_MAJOR  = 3
$MIN_PYTHON_MINOR  = 9

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  =============================================" -ForegroundColor Cyan
    Write-Host "       $APP_NAME - Installer" -ForegroundColor White
    Write-Host "  =============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Number, [string]$Text)
    Write-Host "  [$Number] " -ForegroundColor Green -NoNewline
    Write-Host $Text -ForegroundColor White
}

function Write-Info {
    param([string]$Text)
    Write-Host "      $Text" -ForegroundColor Gray
}

function Write-Success {
    param([string]$Text)
    Write-Host "      [OK] $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "      [!] $Text" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Text)
    Write-Host "      [X] $Text" -ForegroundColor Red
}

function Test-PythonVersion {
    param([string]$PythonPath)
    try {
        $version = & $PythonPath --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge $MIN_PYTHON_MAJOR -and $minor -ge $MIN_PYTHON_MINOR) {
                return $true
            }
        }
    } catch {}
    return $false
}

function Find-Python {
    $candidates = @("python", "python3", "py -3")

    foreach ($cmd in $candidates) {
        try {
            $parts = $cmd -split " "
            if ($parts.Count -eq 1) {
                $result = & $parts[0] --version 2>&1
            } else {
                $result = & $parts[0] $parts[1] --version 2>&1
            }
            if ($result -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -ge $MIN_PYTHON_MAJOR -and $minor -ge $MIN_PYTHON_MINOR) {
                    if ($parts.Count -eq 1) {
                        return $parts[0]
                    } else {
                        return $cmd
                    }
                }
            }
        } catch {}
    }

    $progPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )
    foreach ($p in $progPaths) {
        if (Test-Path $p) {
            if (Test-PythonVersion $p) { return $p }
        }
    }

    return $null
}

# ---------------------------------------------------------------------------
# Main Installer Flow
# ---------------------------------------------------------------------------
Write-Banner

# --- Determine install directory ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

if ($InstallDir -eq "") {
    $DefaultDir = "$env:LOCALAPPDATA\$APP_EXE_NAME"
    if (-not $Silent) {
        Write-Host "  Install location:" -ForegroundColor White
        Write-Host "    Default: $DefaultDir" -ForegroundColor Gray
        $userInput = Read-Host "    Press Enter for default, or type a custom path"
        if ($userInput -ne "") {
            $InstallDir = $userInput
        } else {
            $InstallDir = $DefaultDir
        }
    } else {
        $InstallDir = $DefaultDir
    }
}

Write-Host ""
Write-Info "Install directory: $InstallDir"
Write-Host ""

# =========================================================================
# STEP 1: Check / Install Python
# =========================================================================
Write-Step "1/7" "Checking for Python $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR+ ..."

$PythonCmd = Find-Python

if ($null -eq $PythonCmd) {
    Write-Warn "Python not found. Downloading Python $PYTHON_VERSION ..."

    $TempDir = "$env:TEMP\FormToExcelSetup"
    if (-not (Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir | Out-Null }
    $InstallerPath = "$TempDir\$PYTHON_INSTALLER"

    Write-Info "Downloading from $PYTHON_URL ..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($PYTHON_URL, $InstallerPath)
        Write-Success "Download complete."
    } catch {
        Write-Err "Failed to download Python. Please install Python $PYTHON_VERSION manually."
        Write-Err "Download: https://www.python.org/downloads/"
        Read-Host "Press Enter to exit"
        exit 1
    }

    Write-Info "Installing Python silently (this may take a minute) ..."
    $installArgs = @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_test=0",
        "Include_launcher=1",
        "DefaultJustForMeTargetDir=$env:LOCALAPPDATA\Programs\Python\Python311"
    )
    $process = Start-Process -FilePath $InstallerPath -ArgumentList $installArgs -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        Write-Err "Python installation failed (exit code: $($process.ExitCode))."
        Write-Err "Please install Python manually from https://www.python.org/downloads/"
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    $PythonCmd = Find-Python
    if ($null -eq $PythonCmd) {
        $PythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        if (-not (Test-Path $PythonCmd)) {
            Write-Err "Python was installed but cannot be found. Please restart and try again."
            Read-Host "Press Enter to exit"
            exit 1
        }
    }

    # Cleanup
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Python $PYTHON_VERSION installed successfully."
} else {
    $pyVer = & $PythonCmd --version 2>&1
    Write-Success "Found: $pyVer ($PythonCmd)"
}

Write-Host ""

# =========================================================================
# STEP 2: Create install directory and copy project files
# =========================================================================
Write-Step "2/7" "Setting up application files ..."

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$filesToCopy = @("main.py", "requirements.txt", "README.md")
$dirsToCopy  = @("src")

foreach ($f in $filesToCopy) {
    $src = Join-Path $ProjectRoot $f
    if (Test-Path $src) {
        Copy-Item $src -Destination $InstallDir -Force
    }
}
foreach ($d in $dirsToCopy) {
    $src = Join-Path $ProjectRoot $d
    if (Test-Path $src) {
        Copy-Item $src -Destination $InstallDir -Recurse -Force
    }
}

Write-Success "Application files copied."
Write-Host ""

# =========================================================================
# STEP 3: Create virtual environment
# =========================================================================
Write-Step "3/7" "Creating Python virtual environment ..."

$VenvDir = Join-Path $InstallDir "venv"

if (Test-Path $VenvDir) {
    Write-Info "Existing venv found, removing ..."
    Remove-Item -Path $VenvDir -Recurse -Force
}

& $PythonCmd -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to create virtual environment."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Success "Virtual environment created."
Write-Host ""

# =========================================================================
# STEP 4: Install dependencies
# =========================================================================
Write-Step "4/7" "Installing dependencies (this may take several minutes) ..."
Write-Info "Installing PyTorch CPU + EasyOCR + OpenCV + other packages ..."
Write-Info "Total download: ~800 MB. Please be patient."
Write-Host ""

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

# Upgrade pip first
& $VenvPython -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Info "pip upgraded."

# Install CPU-only PyTorch first (much smaller than GPU version)
Write-Info "Installing PyTorch (CPU-only, ~200 MB) ..."
& $PipExe install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warn "PyTorch install via CPU index failed, trying default ..."
    & $PipExe install torch torchvision --quiet
}
Write-Success "PyTorch installed."

# Install remaining requirements
Write-Info "Installing EasyOCR, OpenCV, and other packages ..."
$ReqFile = Join-Path $InstallDir "requirements.txt"
& $PipExe install -r $ReqFile --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Err "Some dependencies failed to install. Retrying without --quiet ..."
    & $PipExe install -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Dependency installation failed. Check your internet connection."
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Success "All dependencies installed."
Write-Host ""

# =========================================================================
# STEP 5: Pre-download EasyOCR model
# =========================================================================
Write-Step "5/7" "Downloading OCR model (one-time, ~100 MB) ..."

$modelScript = @"
import easyocr
reader = easyocr.Reader(['en'], gpu=False)
print('MODEL_OK')
"@

$modelResult = & $VenvPython -c $modelScript 2>&1
if ($modelResult -match "MODEL_OK") {
    Write-Success "OCR model downloaded and ready."
} else {
    Write-Warn "Model will download on first app launch instead."
}
Write-Host ""

# =========================================================================
# STEP 6: Create launcher and shortcuts
# =========================================================================
Write-Step "6/7" "Creating launcher and shortcuts ..."

# --- Create launcher batch file ---
$LauncherPath = Join-Path $InstallDir "FormToExcel.bat"
$launcherContent = @"
@echo off
title Form To Excel
cd /d "$InstallDir"
call venv\Scripts\activate.bat
start "" pythonw main.py
"@
Set-Content -Path $LauncherPath -Value $launcherContent -Encoding ASCII

# --- Create a VBS wrapper for silent launch (no cmd window flash) ---
$VbsPath = Join-Path $InstallDir "FormToExcel.vbs"
$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "$LauncherPath" & chr(34), 0
Set WshShell = Nothing
"@
Set-Content -Path $VbsPath -Value $vbsContent -Encoding ASCII

Write-Success "Launcher created."

# --- Create Desktop Shortcut ---
try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $DesktopPath = $WScriptShell.SpecialFolders("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "$APP_NAME.lnk"
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "wscript.exe"
    $Shortcut.Arguments = "`"$VbsPath`""
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "$APP_NAME - OCR Form to Excel Tool"
    $Shortcut.Save()
    Write-Success "Desktop shortcut created."
} catch {
    Write-Warn "Could not create desktop shortcut: $_"
}

# --- Create Start Menu Shortcut ---
try {
    $StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$APP_NAME"
    if (-not (Test-Path $StartMenuDir)) {
        New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
    }
    $StartShortcutPath = Join-Path $StartMenuDir "$APP_NAME.lnk"
    $StartShortcut = $WScriptShell.CreateShortcut($StartShortcutPath)
    $StartShortcut.TargetPath = "wscript.exe"
    $StartShortcut.Arguments = "`"$VbsPath`""
    $StartShortcut.WorkingDirectory = $InstallDir
    $StartShortcut.Description = "$APP_NAME - OCR Form to Excel Tool"
    $StartShortcut.Save()
    Write-Success "Start Menu shortcut created."
} catch {
    Write-Warn "Could not create Start Menu shortcut: $_"
}

# --- Create Uninstaller ---
$UninstallerPath = Join-Path $InstallDir "Uninstall.bat"
$uninstallContent = @"
@echo off
echo.
echo  =============================================
echo       Form To Excel - Uninstaller
echo  =============================================
echo.
echo  This will remove Form To Excel from your computer.
echo.
set /p confirm="  Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" goto :cancel

echo.
echo  Removing desktop shortcut ...
del "%USERPROFILE%\Desktop\Form To Excel.lnk" 2>nul

echo  Removing Start Menu entry ...
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Form To Excel" 2>nul

echo  Removing application files ...
cd /d "%TEMP%"
rmdir /s /q "$InstallDir" 2>nul

echo.
echo  [OK] Form To Excel has been uninstalled.
echo.
pause
goto :eof

:cancel
echo.
echo  Uninstall cancelled.
pause
"@
Set-Content -Path $UninstallerPath -Value $uninstallContent -Encoding ASCII
Write-Success "Uninstaller created."
Write-Host ""

# =========================================================================
# STEP 7: Complete
# =========================================================================
Write-Step "7/7" "Installation complete!"
Write-Host ""
Write-Host "  =============================================" -ForegroundColor Green
Write-Host "       Installation Successful!" -ForegroundColor White
Write-Host "  =============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Installed to: $InstallDir" -ForegroundColor Gray
Write-Host ""
Write-Host "  You can launch the app from:" -ForegroundColor White
Write-Host "    - Desktop shortcut: '$APP_NAME'" -ForegroundColor Gray
Write-Host "    - Start Menu: '$APP_NAME'" -ForegroundColor Gray
Write-Host "    - Directly: $LauncherPath" -ForegroundColor Gray
Write-Host ""
Write-Host "  To uninstall, run: $UninstallerPath" -ForegroundColor Gray
Write-Host ""

if (-not $Silent) {
    $launch = Read-Host "  Launch $APP_NAME now? (Y/N)"
    if ($launch -eq "Y" -or $launch -eq "y") {
        Write-Host ""
        Write-Info "Starting $APP_NAME ..."
        Start-Process "wscript.exe" -ArgumentList "`"$VbsPath`""
    }
}

Write-Host ""
Write-Host "  Thank you for installing $APP_NAME!" -ForegroundColor Cyan
Write-Host ""
