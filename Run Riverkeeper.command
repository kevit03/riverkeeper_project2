#!/bin/bash
# Run Riverkeeper dashboard (macOS)

echo "[INFO] Starting Riverkeeper dashboard (macOS)..."

# 1) Go to the folder where this .command file lives (project root)
cd "$(dirname "$0")"

# 2) Create virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment .venv ..."
    python3 -m venv .venv
fi

# 3) Activate the virtual environment
#    (if your default is python, you could also use 'python' above)
source ".venv/bin/activate"

# 4) Install dependencies only on first run (or after deleting the sentinel)
if [ ! -f ".venv/.deps_installed" ]; then
    echo "[INFO] Installing dependencies from requirements.txt (first run) ..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies. Press ENTER to exit."
        read
        exit 1
    fi
    # Mark that dependencies are installed
    touch ".venv/.deps_installed"
else
    echo "[INFO] Dependencies already installed – skipping pip install."
fi

# 5) Call the common Python launcher
echo "[INFO] Running Streamlit via launch.py ..."
python launch.py

# 6) Keep terminal open if something goes wrong
if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Dashboard exited with an error. Press ENTER to close."
    read
fi
