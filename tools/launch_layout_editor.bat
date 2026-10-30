@echo off
cd /d "%~dp0\.."
python tools\layout_editor.py
if errorlevel 1 (
    echo.
    echo Layout Studio could not start. Dependencies: python -m pip install lupa Pillow
    pause
)
