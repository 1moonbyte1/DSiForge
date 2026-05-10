from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent / "project"
PACKAGE_DIR = PROJECT_DIR / "src" / "dsiforge"
__app_name__ = "DSiForge"
__version__ = "0.1.0"

# When this file is discovered as the top-level "dsiforge" module, expose the
# real package path so imports such as "dsiforge.cli" still work from repo root.
__path__ = [str(PACKAGE_DIR)]


def main() -> int:
    commands = {"scan", "report", "backup", "--version", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        from dsiforge.cli import main as cli_main

        return cli_main()

    if len(sys.argv) == 1:
        from dsiforge.state import load_state

        preferred = load_state().settings.preferred_interface
        choice = {"terminal": "1", "gui": "2"}.get(preferred, "")
        if not choice:
            print("Choose DSiForge mode:")
            print("  1 - Terminal UI")
            print("  2 - Desktop GUI")
            choice = input("Press 1 or 2: ").strip()
        if choice == "1":
            from dsiforge.cli import terminal_ui

            return terminal_ui()
        if choice != "2":
            print("Unknown choice. Opening Desktop GUI.")

    from dsiforge.gui import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
