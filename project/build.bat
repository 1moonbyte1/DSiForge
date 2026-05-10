@echo off
setlocal
cd /d "%~dp0"
set ROOT_DIR=%CD%\..

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name DSiForge --windowed --onefile --paths src --hidden-import dsiforge.cli --hidden-import dsiforge.core --hidden-import dsiforge.gui --hidden-import dsiforge.state "%ROOT_DIR%\dsiforge.py"

echo.
echo Build complete. Check the dist folder.
