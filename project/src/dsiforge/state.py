from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


APP_DIR_NAME = "DSiForge"


@dataclass
class AppSettings:
    last_sd_path: str = ""
    default_backup_dir: str = ""
    preferred_interface: str = "ask"
    auto_report_after_scan: bool = False
    compress_backups_by_default: bool = False
    first_run_complete: bool = False


@dataclass
class BackupRecord:
    created_at: str
    source: str
    location: str
    file_count: int
    zipped: bool = False


@dataclass
class AppState:
    settings: AppSettings = field(default_factory=AppSettings)
    backups: list[BackupRecord] = field(default_factory=list)
    last_report_txt: str = ""
    last_report_json: str = ""


def state_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / APP_DIR_NAME
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return path
    except OSError:
        portable = Path.cwd() / ".dsiforge"
        portable.mkdir(parents=True, exist_ok=True)
        return portable


def state_path() -> Path:
    return state_dir() / "state.json"


def load_state() -> AppState:
    path = state_path()
    if not path.exists():
        return AppState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppState()
    settings = AppSettings(**data.get("settings", {}))
    backups = [BackupRecord(**item) for item in data.get("backups", [])]
    return AppState(
        settings=settings,
        backups=backups,
        last_report_txt=data.get("last_report_txt", ""),
        last_report_json=data.get("last_report_json", ""),
    )


def save_state(state: AppState) -> None:
    payload = {
        "settings": asdict(state.settings),
        "backups": [asdict(record) for record in state.backups[-100:]],
        "last_report_txt": state.last_report_txt,
        "last_report_json": state.last_report_json,
    }
    state_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_settings(**changes: object) -> AppState:
    state = load_state()
    for key, value in changes.items():
        if hasattr(state.settings, key):
            setattr(state.settings, key, value)
    save_state(state)
    return state


def add_backup_record(source: str | Path, location: str | Path, file_count: int, zipped: bool = False) -> AppState:
    state = load_state()
    state.backups.append(
        BackupRecord(
            created_at=datetime.now().isoformat(timespec="seconds"),
            source=str(source),
            location=str(location),
            file_count=file_count,
            zipped=zipped,
        )
    )
    state.settings.last_sd_path = str(source)
    state.settings.default_backup_dir = str(Path(location).parent.parent if Path(location).parent.name != "DSiForge_Backups" else Path(location).parent.parent)
    save_state(state)
    return state


def remember_report(txt_path: str | Path | None = None, json_path: str | Path | None = None) -> AppState:
    state = load_state()
    if txt_path:
        state.last_report_txt = str(txt_path)
    if json_path:
        state.last_report_json = str(json_path)
    save_state(state)
    return state


def format_backup_history(limit: int = 10) -> str:
    state = load_state()
    if not state.backups:
        return "No backups recorded yet."
    lines = []
    for record in reversed(state.backups[-limit:]):
        zip_note = " zipped" if record.zipped else ""
        lines.append(f"- {record.created_at}: {record.location} ({record.file_count} files{zip_note})")
    return "\n".join(lines)
