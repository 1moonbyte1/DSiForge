from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core import create_backup, export_report, report_with_backup, scan_sd
from .state import add_backup_record, format_backup_history, load_state, remember_report, update_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dsiforge",
        description="Safe DSi SD card setup checker, backup helper, and report generator.",
    )
    parser.add_argument("--version", action="version", version=f"DSiForge {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    scan = subcommands.add_parser("scan", help="Scan an SD card folder and print a beginner-friendly summary.")
    scan.add_argument("path", help="Path to the SD card root.")

    report = subcommands.add_parser("report", help="Generate a .txt and/or .json recovery report.")
    report.add_argument("path", help="Path to the SD card root.")
    report.add_argument("--txt", help="Output text report path.")
    report.add_argument("--json", help="Output JSON report path.")

    backup = subcommands.add_parser("backup", help="Create a timestamped full SD card backup.")
    backup.add_argument("path", help="Path to the SD card root.")
    backup.add_argument("--output", required=True, help="Backup destination folder.")
    backup.add_argument("--zip", action="store_true", help="Also compress the backup into a .zip archive.")
    backup.add_argument("--important-only", action="store_true", help="Back up only common DSi setup files instead of the full folder.")
    backup.add_argument("--txt", help="Optional text report path to write after backup.")
    backup.add_argument("--json", help="Optional JSON report path to write after backup.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        report = scan_sd(args.path)
        print(report.to_text())
        update_settings(last_sd_path=str(Path(args.path).expanduser()))
        return 0 if report.summary.exists else 2

    if args.command == "report":
        if not args.txt and not args.json:
            print("Choose at least one output: --txt report.txt or --json report.json", file=sys.stderr)
            return 2
        report = scan_sd(args.path)
        export_report(report, args.txt, args.json)
        remember_report(args.txt, args.json)
        outputs = [path for path in (args.txt, args.json) if path]
        print("Wrote report: " + ", ".join(outputs))
        return 0

    if args.command == "backup":
        def progress(done: int, total: int, current: str) -> None:
            print(f"[{done}/{total}] {current}")

        report = scan_sd(args.path)
        backup_dir = create_backup(Path(args.path), Path(args.output), full=not args.important_only, compress=args.zip, progress=progress)
        add_backup_record(args.path, backup_dir, report.summary.file_count, zipped=args.zip)
        if args.txt or args.json:
            report = report_with_backup(report, backup_dir)
            export_report(report, args.txt, args.json)
            remember_report(args.txt, args.json)
        print(f"Created backup: {backup_dir}")
        return 0

    return 2


def terminal_ui() -> int:
    print("DSiForge Terminal UI")
    print("Type help for commands, or exit to quit.")
    state = load_state()
    selected_sd: Path | None = Path(state.settings.last_sd_path) if state.settings.last_sd_path else None
    last_scan = None
    if selected_sd:
        print(f"Last SD root loaded: {selected_sd}")

    while True:
        try:
            raw = input("dsiforge> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            print(f"Could not parse command: {exc}")
            continue

        command = parts[0].lower()
        args = parts[1:]
        if command in {"exit", "quit"}:
            return 0
        if command == "help":
            print(
                "Commands:\n"
                "  use /path/to/sd\n"
                "  status\n"
                "  scan [path]\n"
                "  last-scan\n"
                "  report [path] --txt report.txt [--json report.json]\n"
                "  backup [path] --output backups/ [--zip] [--important-only] [--txt report.txt] [--json report.json]\n"
                "  open-report\n"
                "  prefer ask|terminal|gui\n"
                "  clear\n"
                "  exit\n"
            )
            continue
        if command == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        if command == "status":
            state = load_state()
            print(f"Selected SD root: {selected_sd or 'None'}")
            print(f"Default backup folder: {state.settings.default_backup_dir or 'None'}")
            print(f"Preferred interface: {state.settings.preferred_interface}")
            print("Recent backups:")
            print(format_backup_history(limit=5))
            continue
        if command == "use":
            if not args:
                print("Usage: use /path/to/sd")
                continue
            selected_sd = Path(args[0]).expanduser()
            update_settings(last_sd_path=str(selected_sd))
            print(f"Selected SD root: {selected_sd}")
            continue
        if command == "prefer":
            if not args or args[0] not in {"ask", "terminal", "gui"}:
                print("Usage: prefer ask|terminal|gui")
                continue
            update_settings(preferred_interface=args[0])
            print(f"Preferred interface set to {args[0]}")
            continue
        if command == "last-scan":
            if last_scan is None:
                print("No scan has been run in this terminal session yet.")
            else:
                print(last_scan.to_text())
            continue
        if command == "open-report":
            state = load_state()
            target = state.last_report_txt or state.last_report_json
            if not target:
                print("No exported report is remembered yet.")
                continue
            if _open_path(Path(target)):
                print(f"Opened {target}")
            else:
                print(f"Could not open automatically. Last report: {target}")
            continue

        command_args = args[:]
        if command in {"scan", "report", "backup"} and (not command_args or command_args[0].startswith("-")):
            if selected_sd is None:
                print("No SD root selected. Use: use /path/to/sd")
                continue
            command_args.insert(0, str(selected_sd))

        try:
            if command == "scan":
                scan_path = command_args[0]
                last_scan = scan_sd(scan_path)
                print(last_scan.to_text())
                update_settings(last_sd_path=str(Path(scan_path).expanduser()))
                continue
            exit_code = main([command, *command_args])
        except SystemExit as exc:
            exit_code = int(exc.code or 0)
        except Exception as exc:
            print(f"Command failed: {exc}")
            continue
        if exit_code:
            print(f"Command exited with code {exit_code}")


def _open_path(path: Path) -> bool:
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
