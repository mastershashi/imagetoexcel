; ============================================================================
;  Form To Excel - NSIS Installer Script
;  Creates a single .exe that bundles the entire project and runs the
;  automated setup (Python download, venv, dependencies, shortcuts).
; ============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ---------------------------------------------------------------------------
; General Settings
; ---------------------------------------------------------------------------
Name "Form To Excel"
OutFile "..\dist\FormToExcel_Setup.exe"
InstallDir "$LOCALAPPDATA\FormToExcel"
RequestExecutionLevel user
BrandingText "Form To Excel v1.0"

; ---------------------------------------------------------------------------
; UI Configuration
; ---------------------------------------------------------------------------
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_WELCOMEPAGE_TITLE "Welcome to Form To Excel Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install Form To Excel on your computer.$\r$\n$\r$\nThe installer will automatically:$\r$\n  - Download and install Python (if needed)$\r$\n  - Set up a virtual environment$\r$\n  - Install all required packages$\r$\n  - Download the OCR model$\r$\n  - Create shortcuts$\r$\n$\r$\nInternet connection is required.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Launch Form To Excel"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp

; ---------------------------------------------------------------------------
; Pages
; ---------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ---------------------------------------------------------------------------
; Install Section
; ---------------------------------------------------------------------------
Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy all project files
    File "..\main.py"
    File "..\requirements.txt"
    File "..\README.md"
    File "..\FormToExcel.bat"

    ; Copy source code
    SetOutPath "$INSTDIR\src"
    File /r "..\src\*.*"

    ; Copy installer scripts
    SetOutPath "$INSTDIR\installer"
    File "install.ps1"
    File "install.bat"

    ; Run the PowerShell setup (Python, venv, deps, model)
    SetOutPath "$INSTDIR"
    DetailPrint "Running automated setup (this may take several minutes) ..."
    nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\installer\install.ps1" -InstallDir "$INSTDIR" -Silent'
    Pop $0

    ; Create launcher VBS (silent, no cmd window)
    FileOpen $1 "$INSTDIR\FormToExcel.vbs" w
    FileWrite $1 'Set WshShell = CreateObject("WScript.Shell")$\r$\n'
    FileWrite $1 'WshShell.Run chr(34) & "$INSTDIR\FormToExcel.bat" & chr(34), 0$\r$\n'
    FileWrite $1 'Set WshShell = Nothing$\r$\n'
    FileClose $1

    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\Form To Excel.lnk" \
        "wscript.exe" '"$INSTDIR\FormToExcel.vbs"' \
        "" "" "" "" "Form To Excel - OCR Tool"

    ; Create Start Menu folder and shortcuts
    CreateDirectory "$SMPROGRAMS\Form To Excel"
    CreateShortCut "$SMPROGRAMS\Form To Excel\Form To Excel.lnk" \
        "wscript.exe" '"$INSTDIR\FormToExcel.vbs"' \
        "" "" "" "" "Form To Excel - OCR Tool"
    CreateShortCut "$SMPROGRAMS\Form To Excel\Uninstall.lnk" \
        "$INSTDIR\Uninstall.exe"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "DisplayName" "Form To Excel"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "Publisher" "Form To Excel"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "DisplayVersion" "1.0.0"

    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel" \
        "EstimatedSize" "$0"
SectionEnd

; ---------------------------------------------------------------------------
; Uninstall Section
; ---------------------------------------------------------------------------
Section "Uninstall"
    ; Remove shortcuts
    Delete "$DESKTOP\Form To Excel.lnk"
    RMDir /r "$SMPROGRAMS\Form To Excel"

    ; Remove install directory
    RMDir /r "$INSTDIR"

    ; Remove registry keys
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FormToExcel"
SectionEnd

; ---------------------------------------------------------------------------
; Launch Function
; ---------------------------------------------------------------------------
Function LaunchApp
    Exec 'wscript.exe "$INSTDIR\FormToExcel.vbs"'
FunctionEnd
