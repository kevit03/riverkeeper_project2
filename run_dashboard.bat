@echo off
setlocal ENABLEDELAYEDEXPANSION

echo [INFO] Starting Riverkeeper dashboard (Windows)...

REM 1) Go to the folder where this .bat file lives (project root)
cd /d "%~dp0"

REM 2) Create virtual environment if it does not exist
if not exist ".venv" (
    echo [INFO] Creating virtual environment .venv ...
    py -3 -m venv .venv
)

REM 3) Activate the virtual environment
call ".venv\Scripts\activate.bat"

REM 4) Install required packages
echo [INFO] Installing dependencies from requirements.txt ...
pip install -r requirements.txt

REM 5) Call the common Python launcher
echo [INFO] Running Streamlit via launch.py ...
python launch.py

REM 6) Keep window open if something goes wrong
if errorlevel 1 (
    echo.
    echo [ERROR] Dashboard exited with an error. Press any key to close.
    pause >nul
)

endlocal
