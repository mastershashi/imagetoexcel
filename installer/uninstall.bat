@echo off
title Form To Excel - Uninstaller
echo.
echo  =============================================
echo       Form To Excel - Uninstaller
echo  =============================================
echo.
echo  This will completely remove Form To Excel
echo  from your computer.
echo.
set /p confirm="  Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" goto :cancel

echo.
echo  [1/5] Closing running instances ...
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq Form To Excel" 2>nul
timeout /t 3 /nobreak >nul

echo  [2/5] Removing desktop shortcut ...
del "%USERPROFILE%\Desktop\Form To Excel.lnk" 2>nul

echo  [3/5] Removing Start Menu entry ...
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Form To Excel" 2>nul

echo  [4/5] Removing application files ...
set "INSTALLDIR=%LOCALAPPDATA%\FormToExcel"

if exist "%INSTALLDIR%\venv\Scripts\python.exe" (
    echo         Killing any locked Python processes ...
    for /f "tokens=2" %%p in ('wmic process where "ExecutablePath like '%%FormToExcel%%'" get ProcessId 2^>nul ^| findstr /r "[0-9]"') do (
        taskkill /f /pid %%p 2>nul
    )
    timeout /t 2 /nobreak >nul
)

cd /d "%TEMP%"
rmdir /s /q "%INSTALLDIR%" 2>nul

if exist "%INSTALLDIR%" (
    echo.
    echo  Some files could not be removed. Retrying ...
    timeout /t 3 /nobreak >nul
    rmdir /s /q "%INSTALLDIR%" 2>nul
)

if exist "%INSTALLDIR%" (
    echo.
    echo  [!] Some files are still locked. Please restart your
    echo      computer and delete this folder manually:
    echo      %INSTALLDIR%
) else (
    echo  [5/5] Removing registry entry ...
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" /f 2>nul

    echo.
    echo  =============================================
    echo       Uninstall Complete
    echo  =============================================
    echo.
    echo  Form To Excel has been removed from your computer.
)

echo.
pause
goto :eof

:cancel
echo.
echo  Uninstall cancelled.
echo.
pause
