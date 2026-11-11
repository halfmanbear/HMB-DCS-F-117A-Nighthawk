@echo off
rem F-117 Layout Studio launcher. Double-click to open the editor, or pass
rem arguments through, e.g.: launch_layout_editor.bat --render HUD --output tmp\hud.png
setlocal EnableDelayedExpansion
pushd "%~dp0..\.." || exit /b 1

set "PY="
where py >nul 2>nul && py -3 -c "pass" >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python 3.10 or newer was not found on PATH. Install it from python.org.
    goto :failed
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Layout Studio needs Python 3.10 or newer. Found:
    %PY% --version
    goto :failed
)

set "MISSING="
for %%M in (tkinter lupa PIL) do (
    %PY% -c "import %%M" >nul 2>nul || set "MISSING=!MISSING! %%M"
)
if defined MISSING (
    echo Missing Python modules:!MISSING!
    echo Install lupa and Pillow with: %PY% -m pip install -r tools\cockpit\layout_editor_requirements.txt
    echo tkinter ships with Python; if it is missing, rerun the Python installer and enable tcl/tk.
    goto :failed
)

%PY% tools\cockpit\layout_editor.py %*
set "CODE=%errorlevel%"
popd
if not "%CODE%"=="0" (
    echo.
    echo Layout Studio exited with error code %CODE%.
    if "%~1"=="" pause
)
exit /b %CODE%

:failed
popd
if "%~1"=="" pause
exit /b 1
