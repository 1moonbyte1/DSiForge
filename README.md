# DSiForge

DSiForge is a safe Nintendo DSi SD card setup assistant and backup manager for homebrew users. It helps beginners inspect, back up, and organize an SD card for setups such as TWiLight Menu++, Unlaunch, and hiyaCFW.

DSiForge is not a piracy tool and not a copyrighted-content installer. It checks your files, explains what it finds, creates backups, and exports reports.

## Table Of Contents

- [Safety Promise](#safety-promise)
- [What DSiForge Does](#what-dsiforge-does)
- [Requirements](#requirements)
- [Project Layout](#project-layout)
- [Installation](#installation)
- [Run The App](#run-the-app)
- [Desktop GUI Guide](#desktop-gui-guide)
- [Terminal UI Guide](#terminal-ui-guide)
- [Direct CLI Guide](#direct-cli-guide)
- [Feature Guide](#feature-guide)
- [Backups And Reports](#backups-and-reports)
- [Settings And State](#settings-and-state)
- [Website Guide](#website-guide)
- [Build An Executable](#build-an-executable)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Release Checklist](#release-checklist)
- [License](#license)

## Safety Promise

DSiForge follows these rules:

- Checks are read-only.
- Backups copy files and do not modify the original SD card.
- Existing backup folders are not overwritten.
- Files are not deleted automatically.
- Files are not moved automatically.
- DSiForge does not include ROM downloaders.
- DSiForge does not include copyrighted Nintendo files.
- DSiForge does not include firmware files.
- DSiForge does not include bundled exploit payloads.

Always make a backup before manually changing SD card contents.

## What DSiForge Does

DSiForge can:

- Detect whether a selected folder looks like a DSi SD card.
- Check for `boot.nds`, `_nds`, TWiLight Menu++ folders, config files, themes, saves, and ROM folders.
- Detect misplaced `boot.nds` files.
- Detect empty folders.
- Detect zero-byte files.
- Detect duplicate ROM names.
- Match `.nds` files with `.sav` and `.dsv` save files.
- Report ROMs with no save and saves with no ROM.
- Check common TWiLight theme assets.
- Preview detected PNG theme images in the GUI.
- Create full SD card backups.
- Create optional `.zip` backups.
- Track backup history.
- Export TXT and JSON reports.
- Run as a desktop GUI, Terminal UI, or direct CLI command.

## Official Homebrew Links

Use official releases and documentation for the homebrew projects themselves:

- TWiLight Menu++: https://github.com/DS-Homebrew/TWiLightMenu
- hiyaCFW: https://github.com/DS-Homebrew/hiyaCFW
- Unlaunch information: https://problemkaputt.de/unlaunch.htm

## Requirements

- Python 3.10 or newer
- PySide6 for the desktop GUI

Dependencies are listed in:

```text
project/requirements.txt
```

## Project Layout

The root folder is intentionally clean. The launcher stays at the top, while the rest of the project lives inside `project/`.

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
      download.html
      styles.css
      script.js
      assets/
        dsiforgemenu.png
```

Important files:

- `dsiforge.py`: Main launcher. Run this first.
- `project/src/dsiforge/core.py`: Scanner, backup, reports, theme checks, save matching, and hash helpers.
- `project/src/dsiforge/cli.py`: Direct CLI commands and Terminal UI.
- `project/src/dsiforge/gui.py`: PySide6 desktop GUI.
- `project/src/dsiforge/state.py`: Settings, backup history, and last report tracking.
- `project/website/`: Static website.
- `project/examples/sample-sd/`: Tiny fake SD card layout for testing.

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

## Run The App

From the `DSiForge` folder:

```bash
python dsiforge.py
```

On Windows:

```bat
py dsiforge.py
```

DSiForge asks which interface you want:

```text
Choose DSiForge mode:
  1 - Terminal UI
  2 - Desktop GUI
Press 1 or 2:
```

Press `1` for the Terminal UI. Press `2` for the Desktop GUI.

You can also skip the picker and run direct commands:

```bash
python dsiforge.py scan project/examples/sample-sd
```

## Desktop GUI Guide

The GUI is a dark purple desktop app with a sidebar, action buttons, report panels, progress bars, and real-time logs.

### Dashboard

Use Dashboard to:

- Choose the SD card root.
- Run a scan.
- Start a backup.
- Open the First-run Wizard.
- Read live status messages.
- Watch real-time logs.

### First-run Wizard

The wizard is for beginners. It walks through:

- Choosing an SD card root.
- Running the scan.
- Reviewing warnings.
- Optionally creating a backup.
- Reviewing the report.

### Scan

The Scan page runs the comprehensive checker and shows color-coded results:

- Green means OK.
- Yellow means warning.
- Red means missing, risky, or broken.

### Backup

The Backup page can:

- Back up the full SD card folder.
- Use a default backup location.
- Optionally create a `.zip`.
- Show progress while files are copied.
- Display recent backup history.

### Save/ROM Checker

This page reports:

- ROMs with no matching save.
- Saves with no matching ROM.
- Duplicate ROM names.
- Suspicious save files.

### Theme Tools

This page checks common TWiLight Menu++ theme folders and assets. It can preview detected PNG theme images.

### Reports

The Reports page displays:

- Critical issues.
- Warnings.
- Looks-good items.
- Empty folders.
- Zero-byte files.
- Suggested fixes.

Reports can be exported as TXT or JSON.

### Settings

Settings include:

- Last selected SD path.
- Default backup folder.
- Preferred interface: `ask`, `terminal`, or `gui`.
- Auto-generate reports after scan.
- Compress backups by default.
- Backup history.
- Last report paths.

## Terminal UI Guide

Choose option `1` when starting DSiForge.

You will see:

```text
dsiforge>
```

Type:

```text
help
```

Commands:

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

Example Windows session:

```text
dsiforge> use E:\
dsiforge> scan
dsiforge> backup --output C:\Users\YourName\Backups --zip
dsiforge> report --txt report.txt --json report.json
dsiforge> open-report
dsiforge> exit
```

Example Linux/macOS session:

```text
dsiforge> use /media/username/SDCARD
dsiforge> scan
dsiforge> backup --output ~/DSiForgeBackups
dsiforge> status
dsiforge> exit
```

## Direct CLI Guide

Direct CLI commands are useful for scripts or quick checks.

Scan an SD card:

```bash
python dsiforge.py scan /path/to/sd
```

Scan the included sample:

```bash
python dsiforge.py scan project/examples/sample-sd
```

Export a TXT report:

```bash
python dsiforge.py report /path/to/sd --txt report.txt
```

Export TXT and JSON:

```bash
python dsiforge.py report /path/to/sd --txt report.txt --json report.json
```

Create a full backup:

```bash
python dsiforge.py backup /path/to/sd --output backups/
```

Create a zipped backup:

```bash
python dsiforge.py backup /path/to/sd --output backups/ --zip
```

Back up only common setup files:

```bash
python dsiforge.py backup /path/to/sd --output backups/ --important-only
```

Create a backup and reports:

```bash
python dsiforge.py backup /path/to/sd --output backups/ --txt backup-report.txt --json backup-report.json
```

If you installed the project with `pip install -e project`, you can also use:

```bash
dsiforge scan /path/to/sd
dsiforge report /path/to/sd --txt report.txt
dsiforge backup /path/to/sd --output backups/
dsiforge-gui
```

## Feature Guide

### SD Card Detector

DSiForge checks whether a folder looks like a DSi SD card by looking for:

- `boot.nds`
- `_nds`
- `roms`
- `private`
- TWiLight Menu++ folders

It reports:

- Total files.
- Total folders.
- Free space.
- Top-level folders.
- ROM count.
- Save count.
- Config file count.
- Theme asset count.

### Comprehensive Scan

The scan checks:

- `boot.nds` at SD root.
- `_nds` folder.
- TWiLight Menu++ folders.
- Common folders such as `roms`, `saves`, and `private`.
- Empty folders.
- Zero-byte files.
- Misplaced `boot.nds`.
- Suspicious duplicate setup files.
- Duplicate ROM names.
- Save/ROM mismatches.
- Optional SHA-256 checks if hashes are provided in future scripts.

### Save Matching

The save matcher looks at:

- `.nds`
- `.sav`
- `.dsv`

It normalizes names and reports:

- ROMs without saves.
- Saves without ROMs.
- Suspicious save files.
- Duplicate ROM filenames.

### Theme Tools

Theme Tools checks common theme folders such as:

```text
_nds/TWiLightMenu/themes/
_nds/TwilightMenu/themes/
themes/
```

It looks for common assets:

- `background.png`
- `top.png`
- `bottom.png`
- `settings.ini`

PNG dimensions are read directly from the file header, so no extra image library is required.

### Organizer Suggestions

DSiForge detects common file types:

- `.nds`
- `.sav`
- `.dsv`
- `.png`
- `.bmp`
- `.ini`
- `.json`
- `.txt`

It suggests better folders when files look misplaced. Suggestions are not actions. DSiForge does not move files automatically.

## Backups And Reports

Backups are stored like this:

```text
DSiForge_Backups/YYYY-MM-DD_HH-MM-SS/
```

Example:

```text
DSiForge_Backups/2026-05-10_16-11-03/
```

Backup behavior:

- Full backups copy the selected SD card folder.
- `--important-only` copies common setup files and folders.
- `--zip` creates an archive.
- A backup manifest is written.
- Existing backup folders are not overwritten.
- The original SD card folder is not modified.

Reports can be exported as:

- `.txt` for people.
- `.json` for tools.

Reports include:

- Total files scanned.
- Total folders scanned.
- Config and theme counts.
- Missing files and folders.
- Empty folders.
- Zero-byte files.
- Duplicate ROM names.
- Save/ROM mismatches.
- Theme warnings.
- Backup location confirmation.
- Suggested fix steps.

## Settings And State

DSiForge stores lightweight local state:

- Last selected SD path.
- Default backup folder.
- Preferred interface.
- Auto-report setting.
- Compress-backups setting.
- Backup history.
- Last exported report paths.

Typical state location:

- Windows: `%APPDATA%\DSiForge\state.json`
- Linux/macOS: `~/.config/DSiForge/state.json`

If the user config folder is not writable, DSiForge falls back to:

```text
.dsiforge/state.json
```

## Website Guide

The static website lives in:

```text
project/website/
```

Pages:

- `project/website/index.html`
- `project/website/download.html`

Assets:

- `project/website/assets/dsiforgemenu.png`

The download button points to:

```text
https://github.com/1moonbyte1/DSiForge
```

The URL is configured in:

```text
project/website/script.js
```

To preview the website, open:

```text
project/website/index.html
```

No web server is required.

## Build An Executable

### Build With The Included Scripts

Windows:

```bat
project\build.bat
```

Linux/macOS:

```bash
./project/build.sh
```

The generated executable will be placed in:

```text
project/dist/
```

### Manual PyInstaller Build

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the launcher app:

```bash
cd project
pyinstaller --name DSiForge --windowed --onefile --paths src --hidden-import dsiforge.cli --hidden-import dsiforge.core --hidden-import dsiforge.gui --hidden-import dsiforge.state ../dsiforge.py
```

Build a CLI-focused executable:

```bash
cd project
pyinstaller --name dsiforge --onefile --paths src src/dsiforge/cli.py
```

## Testing

Compile check:

```bash
python -m py_compile dsiforge.py project/src/dsiforge/core.py project/src/dsiforge/cli.py project/src/dsiforge/gui.py project/src/dsiforge/state.py
```

Scan the sample SD card:

```bash
python dsiforge.py scan project/examples/sample-sd
```

Create a sample backup on Linux/macOS:

```bash
python dsiforge.py backup project/examples/sample-sd --output /tmp
```

Create a sample backup on Windows:

```bat
py dsiforge.py backup project\examples\sample-sd --output %USERPROFILE%\Desktop
```

Open Terminal UI:

```bash
python dsiforge.py
```

Then press `1`.

## Troubleshooting

### PySide6 is missing

Install dependencies:

```bash
pip install -r project/requirements.txt
```

### The GUI does not open on Linux

Make sure your desktop session supports Qt applications. If you are using a headless terminal or SSH session, use Terminal UI instead.

### The app opens Terminal UI automatically

The preferred interface may be set to `terminal`. In Terminal UI, run:

```text
prefer ask
```

### The app opens GUI automatically

The preferred interface may be set to `gui`. In Terminal UI, run:

```text
prefer ask
```

### Backup fails because a folder already exists

DSiForge refuses to overwrite existing backup folders. Choose a different output folder or try again later so the timestamp is different.

### The SD card is not detected

Make sure you selected the SD card root, not a subfolder. The root is usually the folder containing items like `boot.nds`, `_nds`, `roms`, or `private`.

### Windows Command Prompt clear command

The Terminal UI `clear` command uses `cls` on Windows and `clear` on Linux/macOS.

## Release Checklist

Before publishing a release:

- Run the compile check.
- Run a sample scan.
- Run a sample backup.
- Open the GUI locally if a display is available.
- Open `project/website/index.html`.
- Open `project/website/download.html`.
- Confirm the GitHub download URL is correct.
- Build with `project\build.bat` or `./project/build.sh`.
- Confirm the executable starts.
- Confirm no generated backup folders, `.dsiforge` state, or `__pycache__` folders are committed by mistake.

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

DSiForge is licensed under the MIT License. See:

```text
project/LICENSE
```
