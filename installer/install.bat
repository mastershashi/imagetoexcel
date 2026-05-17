@echo off
:: ============================================================================
::  Form To Excel - Installer Launcher
::  This script runs the PowerShell installer with proper permissions.
:: ============================================================================

title Form To Excel - Installer

echo.
echo   =============================================
echo        Form To Excel - Installer
echo   =============================================
echo.
echo   This will install Form To Excel on your computer.
echo   The installer will:
echo     1. Check for / install Python
echo     2. Set up a virtual environment
echo     3. Install all required packages
echo     4. Download the OCR model
echo     5. Create desktop and Start Menu shortcuts
echo.
echo   Internet connection required for first-time setup.
echo.
pause

:: Check if running as admin for Python install
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo   Note: Some features may need administrator access.
    echo   If Python installation fails, right-click this file
    echo   and select "Run as administrator".
    echo.
)

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

:: Run the PowerShell installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1"

if %errorLevel% neq 0 (
    echo.
    echo   Installation encountered an error.
    echo   Please check the messages above for details.
    echo.
    pause
)
