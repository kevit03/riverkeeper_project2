#!/bin/bash
# Run Riverkeeper dashboard (Docker, macOS)

echo "[INFO] Starting Riverkeeper dashboard (Docker, macOS)..."

# 1) Go to the folder where this .command file lives (project root)
cd "$(dirname "$0")"

# 2) Check that Docker is installed
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker is not installed or not on PATH."
    echo "Please install Docker Desktop for Mac and try again."
    read -p "Press ENTER to exit..."
    exit 1
fi

# 3) Check that Docker Desktop is running
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker Desktop does not appear to be running."
    echo "Please open Docker Desktop, wait until it says 'Docker is running',"
    echo "then run this file again."
    read -p "Press ENTER to exit..."
    exit 1
fi

# 4) Build the image if it doesn't exist yet
if ! docker image inspect riverkeeper-dashboard:latest >/dev/null 2>&1; then
    echo "[INFO] Docker image not found. Building riverkeeper-dashboard..."
    docker build -t riverkeeper-dashboard .
    if [ $? -ne 0 ]; then
        echo "[ERROR] Docker build failed."
        read -p "Press ENTER to exit..."
        exit 1
    fi
else
    echo "[INFO] Docker image riverkeeper-dashboard already exists – skipping build."
fi

# 5) Run the container in the background
echo "[INFO] Starting dashboard at http://localhost:8501 ..."
docker run --rm -p 8501:8501 riverkeeper-dashboard &
CONTAINER_PID=$!

# 6) Give Streamlit a few seconds to start, then open browser
sleep 5
echo "[INFO] Opening browser..."
open "http://localhost:8501"

# 7) Wait for the container to exit
wait $CONTAINER_PID
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "[ERROR] Docker container exited with error code $EXIT_CODE."
    read -p "Press ENTER to close..."
else
    echo
    echo "[INFO] Dashboard stopped. You can now close this window."
    read -p "Press ENTER to close..."
fi
