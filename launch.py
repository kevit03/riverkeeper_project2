import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    app_path = project_root / "functions" / "front.py"

    # Safety: check the file exists
    if not app_path.exists():
        print(f"[ERROR] Could not find Streamlit app at {app_path}")
        sys.exit(1)

    # Run: python -m streamlit run functions/front.py
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    print("[INFO] Executing:", " ".join(cmd))
    subprocess.run(cmd, check=True)
