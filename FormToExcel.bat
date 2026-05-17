@echo off
:: Quick launcher for development (runs from project directory)
title Form To Excel
cd /d "%~dp0"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    start "" pythonw main.py
) else (
    echo Virtual environment not found. Running with system Python ...
    start "" python main.py
)
