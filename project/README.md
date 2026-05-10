# DSiForge

DSiForge is a safe homebrew setup assistant and SD card manager for Nintendo DSi users. It helps beginners inspect, back up, and organize a DSi SD card for homebrew setups such as TWiLight Menu++, Unlaunch, and hiyaCFW.

DSiForge is not a modding shortcut tool. It does not install copyrighted files, download ROMs, include firmware, or ship exploit payloads. Its job is to check your SD card, explain what it finds, create backups, and generate reports.

## Main Safety Rules

- DSiForge checks are read-only.
- DSiForge never deletes files automatically.
- DSiForge never moves files automatically.
- Backups copy files and do not modify the original SD card.
- Existing backup folders are not overwritten.
- DSiForge does not include piracy tools, ROM downloaders, copyrighted Nintendo files, firmware files, or exploit payloads.

Always make a backup before manually changing SD card contents.

## Official Project Links

Use official releases and documentation for the homebrew projects themselves:

- TWiLight Menu++: https://github.com/DS-Homebrew/TWiLightMenu
- hiyaCFW: https://github.com/DS-Homebrew/hiyaCFW
- Unlaunch information: https://problemkaputt.de/unlaunch.htm

## Requirements

- Python 3.10 or newer
- PySide6 for the desktop GUI

Install dependencies with:

```bash
pip install -r project/requirements.txt
```

## Installation

### Windows PowerShell

```powershell
cd DSiForge
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r project\requirements.txt
pip install -e project
```

### Windows Command Prompt

```bat
cd DSiForge
py -m venv .venv
.venv\Scripts\activate
pip install -r project\requirements.txt
pip install -e project
```

### Linux / macOS

```bash
cd DSiForge
python -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
pip install -e project
```

## How To Run DSiForge

### Mode Picker

Run this from the `DSiForge` folder:

```bash
python dsiforge.py
```

On Windows you can also use:

```bat
py dsiforge.py
```

DSiForge will ask which interface you want:

```text
Choose DSiForge mode:
  1 - Terminal UI
  2 - Desktop GUI
Press 1 or 2:
```

Press `1` for the Terminal UI. Press `2` for the Desktop GUI.

### Desktop GUI

The desktop GUI has a modern dark purple interface with:

- Sidebar navigation
- Dashboard
- Scan page
- Backup page
- Save/ROM Checker
- Theme Tools
- Reports
- Settings
- Progress bars for scans and backups
- Real-time logs
- Success, warning, and failure notifications
- First-run wizard for beginners
- Backup history
- Theme image preview for detected PNG assets
- Settings for default backup folder, preferred interface, auto reports, and zip backups
- Color-coded results:
  - Green means OK
  - Yellow means warning
  - Red means missing, risky, or broken

You can also run the installed GUI command:

```bash
dsiforge-gui
```

### Terminal UI

Choose option `1` in the mode picker to open:

```text
dsiforge>
```

Type:

```text
help
```

Available Terminal UI commands:

```text
use /path/to/sd
status
scan [path]
last-scan
report [path] --txt report.txt [--json report.json]
backup [path] --output backups/ [--zip] [--important-only] [--txt report.txt] [--json report.json]
open-report
prefer ask|terminal|gui
clear
exit
```

Example Terminal UI session:

```text
dsiforge> use E:\
dsiforge> status
dsiforge> scan
dsiforge> last-scan
dsiforge> backup --output C:\Users\YourName\Backups
dsiforge> report --txt report.txt --json report.json
dsiforge> open-report
dsiforge> exit
```

### Direct CLI Commands

You can skip the mode picker and run commands directly.

Scan an SD card:

```bash
dsiforge scan /path/to/sd
```

Without installing:

```bash
python dsiforge.py scan project/examples/sample-sd
```

Export a text report:

```bash
dsiforge report /path/to/sd --txt report.txt
```

Export both text and JSON reports:

```bash
dsiforge report /path/to/sd --txt report.txt --json report.json
```

Create a full SD card backup:

```bash
dsiforge backup /path/to/sd --output backups/
```

Create a zipped backup and reports:

```bash
dsiforge backup /path/to/sd --output backups/ --zip --txt backup-report.txt --json backup-report.json
```

Back up only common setup files instead of the whole folder:

```bash
dsiforge backup /path/to/sd --output backups/ --important-only
```

## Feature Guide

### 1. SD Card Detector

DSiForge lets you choose an SD card root folder. It checks whether the folder looks like a DSi SD card by looking for common items such as:

- `boot.nds`
- `_nds`
- `roms`
- `private`
- TWiLight Menu++ folders

It also reports:

- Total files
- Total folders
- Free space
- Top-level folders
- ROM count
- Save count
- Config file count
- Theme asset count

### 2. Comprehensive Scan

The scan checks for common setup issues:

- `boot.nds` at the SD card root
- `_nds` folder
- TWiLight Menu++ folders
- `roms`, `saves`, `themes`, and config files
- Empty folders
- Zero-byte files
- Duplicate ROM filenames
- Missing save files
- Save files with no matching ROM
- `boot.nds` accidentally placed inside a subfolder
- Common files that look duplicated

Optional SHA-256 hash helpers exist in the core scanner for checking critical files if known-good hashes are provided by future code or scripts.

The GUI report viewer groups results into:

- Critical
- Warnings
- Looks Good
- Save/ROM Checker
- Empty folders
- Zero-byte files
- Suggested fixes

### 3. Backup System

The Backup page and `backup` CLI command copy the full SD card folder into a timestamped backup directory:

```text
DSiForge_Backups/YYYY-MM-DD_HH-MM-SS/
```

Example:

```text
DSiForge_Backups/2026-05-10_16-11-03/
```

Backup features:

- Copies the full selected SD card folder
- Can optionally copy only common setup files with `--important-only`
- Shows progress in the GUI
- Prints progress in the CLI
- Writes a backup manifest
- Can optionally create a `.zip`
- Does not overwrite an existing timestamped backup folder
- Does not modify the original SD card
- Saves backup history in the local DSiForge state file

### 4. Save/ROM Checker

The Save/ROM Checker scans `.nds`, `.sav`, and `.dsv` files.

It reports:

- ROMs with no matching save
- Saves with no matching ROM
- Duplicate ROM filenames
- Suspicious save files, such as zero-byte saves or oddly sized saves

DSiForge does not rename, move, or delete saves. It only reports what it finds.

### 5. Theme Tools

Theme Tools checks common TWiLight Menu++ theme folders and looks for common theme assets:

- `background.png`
- `top.png`
- `bottom.png`
- `settings.ini`

It also reads PNG dimensions directly from the image header and warns about unusually large images.

The GUI shows a simple preview of detected PNG theme images when possible.

### 6. Homebrew Organizer Suggestions

DSiForge detects common file types:

- `.nds`
- `.sav`
- `.dsv`
- `.png`
- `.bmp`
- `.ini`
- `.json`
- `.txt`

It suggests better folders when files look misplaced. Suggestions are only suggestions. DSiForge does not move files automatically.

### 7. Reports

Reports can be exported as `.txt` and `.json`.

Reports include:

- Total files scanned
- Total folders scanned
- Config and theme counts
- Missing files and folders
- Empty folders
- Zero-byte files
- Duplicate ROM names
- Save/ROM mismatches
- Theme warnings
- Backup location confirmation after backup
- Suggested fix steps

### 8. First-run Wizard

The First-run Wizard is available from the Dashboard. It guides beginners through:

- Choosing the SD card root
- Running the scan
- Reviewing warnings
- Optionally creating a backup
- Reviewing the Reports page

### 9. Settings And Backup History

DSiForge stores lightweight local state:

- Last selected SD path
- Default backup folder
- Preferred interface: `ask`, `terminal`, or `gui`
- Auto-generate reports after scan
- Compress backups by default
- Backup history
- Last exported report paths

On most systems this is stored in the user config folder. If that folder is not writable, DSiForge falls back to a portable `.dsiforge/` folder in the current working directory.

## Project Layout

```text
DSiForge/
  dsiforge.py
  project/
    README.md
    LICENSE
    requirements.txt
    pyproject.toml
    build.bat
    build.sh
    src/
      dsiforge/
        __init__.py
        __main__.py
        core.py
        cli.py
        gui.py
        state.py
    examples/
      README.md
      sample-sd/
        boot.nds
        _nds/
        roms/
    screenshots/
      README.md
    website/
      index.html
      styles.css
      script.js
      assets/
```

### Important Files

- `dsiforge.py`: Main launcher. This is the only file kept at the project root.
- `project/src/dsiforge/core.py`: Shared scan, report, backup, hash, theme, and save matching logic.
- `project/src/dsiforge/cli.py`: Direct CLI commands and Terminal UI.
- `project/src/dsiforge/gui.py`: PySide6 desktop GUI.
- `project/src/dsiforge/state.py`: Settings, backup history, and last report tracking.
- `project/requirements.txt`: Python dependencies.
- `project/pyproject.toml`: Package metadata and console commands.
- `project/build.bat`: One-command Windows PyInstaller build.
- `project/build.sh`: One-command Linux/macOS PyInstaller build.
- `project/examples/sample-sd/`: Tiny fake SD card layout for testing.
- `project/screenshots/`: Place GUI screenshots here.
- `project/website/`: Static website for DSiForge.

## Website

The website is a static HTML/CSS/JS site in:

```text
project/website/
```

Open this file in a browser:

```text
project/website/index.html
```

The download page is:

```text
project/website/download.html
```

It uses the real app menu screenshot stored at:

```text
project/website/assets/dsiforgemenu.png
```

The website download button points to:

```text
https://github.com/1moonbyte1/DSiForge
```

The URL is configured in:

```text
project/website/script.js
```

## Testing With The Included Sample

Run:

```bash
python dsiforge.py scan project/examples/sample-sd
```

Create a test backup:

```bash
python dsiforge.py backup project/examples/sample-sd --output /tmp
```

On Windows, choose a folder you can write to:

```bat
py dsiforge.py backup project\examples\sample-sd --output %USERPROFILE%\Desktop
```

## Build A Windows .exe With PyInstaller

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the GUI/launcher app:

```bash
cd project
pyinstaller --name DSiForge --windowed --onefile --paths src --hidden-import dsiforge.cli --hidden-import dsiforge.core --hidden-import dsiforge.gui --hidden-import dsiforge.state ../dsiforge.py
```

Or use the included build script on Windows:

```bat
project\build.bat
```

On Linux/macOS:

```bash
./project/build.sh
```

The generated executable will be placed in:

```text
project/dist/
```

Build a CLI-focused executable:

```bash
cd project
pyinstaller --name dsiforge --onefile --paths src src/dsiforge/cli.py
```

## Screenshots

Screenshots belong in:

```text
project/screenshots/
```

Suggested screenshot names:

- `dashboard.png`
- `scan.png`
- `backup.png`
- `save-rom-checker.png`
- `reports.png`

## License

DSiForge is licensed under the MIT License. See `project/LICENSE`.
