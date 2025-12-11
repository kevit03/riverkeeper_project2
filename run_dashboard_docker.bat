@echo off
setlocal ENABLEDELAYEDEXPANSION

echo [INFO] Starting Riverkeeper dashboard (Docker, Windows)...

REM 1) Go to the folder where this .bat file lives (project root)
cd /d "%~dp0"

REM 2) Check Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not on PATH.
    echo Please install Docker Desktop for Windows and try again.
    echo.
    pause
    exit /b 1
)

REM 3) Check Docker engine is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker does not appear to be running.
    echo Please open Docker Desktop, wait until it says "Docker is running",
    echo then run this file again.
    echo.
    pause
    exit /b 1
)

REM 4) Build the image if it doesn't exist yet
docker image inspect riverkeeper-dashboard:latest >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker image not found. Building riverkeeper-dashboard...
    docker build -t riverkeeper-dashboard .
    if errorlevel 1 (
        echo [ERROR] Docker build failed.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Docker image riverkeeper-dashboard already exists - skipping build.
)

REM 5) Start the container in a separate window
echo [INFO] Starting dashboard at http://localhost:8501 ...
start "Riverkeeper Docker" cmd /c "docker run --rm -p 8501:8501 riverkeeper-dashboard"

REM 6) Give Streamlit a few seconds to boot, then open browser
timeout /t 5 /nobreak >nul
echo [INFO] Opening browser...
start "" http://localhost:8501

echo.
echo [INFO] The Riverkeeper dashboard should now be open in your browser.
echo [INFO] To stop it, close the browser tab AND the 'Riverkeeper Docker' window.
echo.
pause
endlocal

