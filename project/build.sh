#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT_DIR="$(pwd)/.."

if [ ! -d .venv ]; then
  python -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller \
  --name DSiForge \
  --windowed \
  --onefile \
  --paths src \
  --hidden-import dsiforge.cli \
  --hidden-import dsiforge.core \
  --hidden-import dsiforge.gui \
  --hidden-import dsiforge.state \
  "$ROOT_DIR/dsiforge.py"

echo "Build complete. Check the dist folder."
