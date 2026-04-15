@echo off
setlocal ENABLEDELAYEDEXPANSION

echo [INFO] Starting Riverkeeper Dash dashboard - Windows ...

REM 1) Go to the folder where this .bat file lives (project root)
cd /d "%~dp0"

REM 2) Create virtual environment if it does not exist
if not exist ".venv" (
    echo [INFO] Creating virtual environment .venv ...
    py -3 -m venv .venv
)

REM 3) Activate the virtual environment
call ".venv\Scripts\activate.bat"

REM 4) Install dependencies only on first run
if not exist ".venv\.deps_installed" (
    echo [INFO] Installing dependencies from requirements.txt ...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies. Press any key to close.
        pause >nul
        goto :end
    )
    > ".venv\.deps_installed" echo ok
) else (
    echo [INFO] Dependencies already installed - skipping pip install.
)

REM 5) Launch the Dash app
echo [INFO] Launching Dash app on http://127.0.0.1:8050 ...
python -m dash_app.app

REM 6) Keep window open so user can see errors
if errorlevel 1 (
    echo.
    echo [ERROR] Dashboard exited with an error. Press any key to close.
    pause >nul
) else (
    echo.
    echo [INFO] Dashboard closed normally. Press any key to exit.
    pause >nul
)

:end
endlocal
