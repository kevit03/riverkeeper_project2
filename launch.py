#!/usr/bin/env python3
"""
Common launcher for the Riverkeeper Streamlit app.

Used by:
- Run Riverkeeper.command (macOS)
- run_dashboard.bat (Windows)
"""

from pathlib import Path
import subprocess
import sys

# Project root (folder containing this file)
ROOT = Path(__file__).resolve().parent

# Path to the Streamlit app (UPDATE: app/front.py, not functions/front.py)
APP_PATH = ROOT / "app" / "front.py"

if not APP_PATH.exists():
    print(f"[ERROR] Could not find Streamlit app at {APP_PATH}")
    sys.exit(1)

def main() -> int:
    cmd = ["streamlit", "run", str(APP_PATH)]
    print(f"[INFO] Executing: {' '.join(cmd)}")
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
