#!/usr/bin/env bash
set -e  # exit on first error

# Always start from the project root
cd "$(dirname "$0")"

# Create venv only once
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip

  # Force pyarrow to use a binary wheel (no CMake build)
  pip install "pyarrow==16.1.0" --only-binary=:all:

  # Install the rest
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

# TODO: CHANGE THIS TO YOUR REAL STREAMLIT FILE
streamlit run app/front.py
