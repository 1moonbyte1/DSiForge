from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable


KNOWN_TYPES = {".nds", ".sav", ".dsv", ".png", ".bmp", ".ini", ".json", ".txt"}
SAVE_TYPES = {".sav", ".dsv"}
TEXT_TYPES = {".ini", ".json", ".txt"}
TWILIGHT_HINTS = ("_nds", "roms", "title", "themes")
COMMON_FOLDERS = ("_nds", "roms", "saves", "private")
THEME_ASSETS = ("background.png", "top.png", "bottom.png", "settings.ini")
ProgressCallback = Callable[[int, int, str], None]


@dataclass
class CheckItem:
    level: str
    title: str
    detail: str
    path: str | None = None
    suggestion: str | None = None


@dataclass
class SdSummary:
    root: str
    exists: bool
    looks_like_dsi_sd: bool
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    folder_count: int = 0
    file_count: int = 0
    config_count: int = 0
    theme_count: int = 0
    rom_count: int = 0
    save_count: int = 0
    top_level_folders: list[str] = field(default_factory=list)


@dataclass
class SaveMatchReport:
    rom_count: int = 0
    save_count: int = 0
    duplicate_rom_names: list[str] = field(default_factory=list)
    roms_without_saves: list[str] = field(default_factory=list)
    saves_without_roms: list[str] = field(default_factory=list)
    suspicious_saves: list[str] = field(default_factory=list)


@dataclass
class ThemeReport:
    theme_root: str
    checked_folders: int = 0
    items: list[CheckItem] = field(default_factory=list)


@dataclass
class OrganizerSuggestion:
    path: str
    extension: str
    suggested_folder: str
    reason: str


@dataclass
class ScanReport:
    generated_at: str
    summary: SdSummary
    setup_items: list[CheckItem]
    theme_report: ThemeReport
    save_report: SaveMatchReport
    organizer_suggestions: list[OrganizerSuggestion]
    empty_folders: list[str] = field(default_factory=list)
    zero_byte_files: list[str] = field(default_factory=list)
    hash_results: dict[str, str] = field(default_factory=dict)
    backup_location: str | None = None

    @property
    def good(self) -> list[CheckItem]:
        return [item for item in self.setup_items if item.level == "good"]

    @property
    def missing(self) -> list[CheckItem]:
        return [item for item in self.setup_items if item.level == "missing"]

    @property
    def risky(self) -> list[CheckItem]:
        return [item for item in self.setup_items if item.level in {"warning", "risk"}]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_text(self) -> str:
        lines = [
            "DSiForge Recovery Report",
            f"Generated: {self.generated_at}",
            f"SD root: {self.summary.root}",
            f"Total files scanned: {self.summary.file_count}",
            f"Total folders scanned: {self.summary.folder_count}",
            f"Config files detected: {self.summary.config_count}",
            f"Theme assets detected: {self.summary.theme_count}",
        ]
        if self.backup_location:
            lines.append(f"Backup location: {self.backup_location}")
        lines.extend(["", "What looks good"])
        lines.extend(_format_items(self.good, "No confirmed setup items yet."))
        lines.append("")
        lines.append("What is missing")
        lines.extend(_format_items(self.missing, "No required folders/files appear missing."))
        lines.append("")
        lines.append("What might be risky")
        risky_items = self.risky + [item for item in self.theme_report.items if item.level != "good"]
        lines.extend(_format_items(risky_items, "No obvious risks found."))
        lines.append("")
        lines.append("Save/ROM checker")
        lines.append(f"- ROM files found: {self.save_report.rom_count}")
        lines.append(f"- Save files found: {self.save_report.save_count}")
        if self.save_report.roms_without_saves:
            lines.append("- ROMs with no matching save:")
            lines.extend(f"  - {path}" for path in self.save_report.roms_without_saves)
        if self.save_report.saves_without_roms:
            lines.append("- Saves with no matching ROM:")
            lines.extend(f"  - {path}" for path in self.save_report.saves_without_roms)
        if self.save_report.duplicate_rom_names:
            lines.append("- Duplicate ROM names:")
            lines.extend(f"  - {path}" for path in self.save_report.duplicate_rom_names)
        if self.empty_folders:
            lines.append("")
            lines.append("Empty folders")
            lines.extend(f"- {path}" for path in self.empty_folders)
        if self.zero_byte_files:
            lines.append("")
            lines.append("Zero-byte files")
            lines.extend(f"- {path}" for path in self.zero_byte_files)
        lines.append("")
        lines.append("Suggested fix steps")
        lines.extend(suggest_fix_steps(self))
        return "\n".join(lines) + "\n"


def scan_sd(root: str | Path, critical_hashes: dict[str, str] | None = None) -> ScanReport:
    sd_root = Path(root).expanduser().resolve()
    summary = summarize_sd(sd_root)
    setup_items = check_setup(sd_root)
    save_report = match_saves(sd_root)
    theme_report = check_themes(sd_root)
    suggestions = suggest_organization(sd_root)
    empty_folders = find_empty_folders(sd_root)
    zero_byte_files = find_zero_byte_files(sd_root)
    hash_results = verify_hashes(sd_root, critical_hashes or {})

    for folder in empty_folders[:100]:
        setup_items.append(CheckItem("warning", "Empty folder", "This folder has no files or subfolders.", folder))
    for duplicate in save_report.duplicate_rom_names:
        setup_items.append(CheckItem("warning", "Duplicate ROM name", "Another .nds file has the same filename.", duplicate))
    for path, result in hash_results.items():
        level = "good" if result == "OK" else "risk"
        setup_items.append(CheckItem(level, "SHA-256 verification", result, path))

    return ScanReport(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        summary=summary,
        setup_items=setup_items,
        theme_report=theme_report,
        save_report=save_report,
        organizer_suggestions=suggestions,
        empty_folders=empty_folders,
        zero_byte_files=zero_byte_files,
        hash_results=hash_results,
    )


def summarize_sd(root: Path) -> SdSummary:
    if not root.exists() or not root.is_dir():
        return SdSummary(str(root), False, False)

    usage = shutil.disk_usage(root)
    files = list(_safe_walk_files(root))
    folders = [path for path in root.rglob("*") if path.is_dir()]
    top_folders = sorted(path.name for path in root.iterdir() if path.is_dir())
    names = {name.lower() for name in top_folders}
    root_files = {path.name.lower() for path in root.iterdir() if path.is_file()}
    looks_like = bool(
        {"_nds", "roms", "private"} & names
        or "boot.nds" in root_files
        or any(hint in names for hint in TWILIGHT_HINTS)
    )
    return SdSummary(
        root=str(root),
        exists=True,
        looks_like_dsi_sd=looks_like,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        folder_count=len(folders),
        file_count=len(files),
        config_count=sum(1 for path in files if path.suffix.lower() in TEXT_TYPES),
        theme_count=sum(1 for path in files if path.suffix.lower() in {".png", ".bmp", ".ini"} and "theme" in str(path.parent).lower()),
        rom_count=sum(1 for path in files if _looks_like_rom(path, root)),
        save_count=sum(1 for path in files if path.suffix.lower() in SAVE_TYPES),
        top_level_folders=top_folders,
    )


def check_setup(root: Path) -> list[CheckItem]:
    items: list[CheckItem] = []
    if not root.exists():
        return [CheckItem("risk", "Path does not exist", "Choose a real SD card root folder.", str(root))]

    boot = root / "boot.nds"
    if boot.is_file():
        items.append(CheckItem("good", "boot.nds found", "The expected root boot file is present.", str(boot)))
    else:
        items.append(
            CheckItem(
                "missing",
                "boot.nds missing at root",
                "Many DSi homebrew setups expect boot.nds directly on the SD root.",
                str(boot),
                "Download TWiLight Menu++ from its official open-source release page and place boot.nds at the SD root.",
            )
        )

    nds_dir = root / "_nds"
    if nds_dir.is_dir():
        items.append(CheckItem("good", "_nds folder found", "TWiLight Menu++ support files usually live here.", str(nds_dir)))
    else:
        items.append(CheckItem("missing", "_nds folder missing", "This folder is common in TWiLight Menu++ setups.", str(nds_dir)))

    twilight_dirs = [root / "_nds" / "TWiLightMenu", root / "_nds" / "TwilightMenu", root / "TWiLightMenu"]
    if any(path.exists() for path in twilight_dirs):
        items.append(CheckItem("good", "TWiLight Menu++ folders detected", "A known TWiLight folder name was found."))
    else:
        items.append(CheckItem("missing", "TWiLight Menu++ folders not detected", "Could not find common TWiLight Menu++ folders."))

    for folder in COMMON_FOLDERS:
        path = root / folder
        if path.exists():
            items.append(CheckItem("good", f"Folder detected: {folder}", "Common SD card folder is present.", str(path)))
        else:
            items.append(CheckItem("warning", f"Common folder missing: {folder}", "This may be normal, but beginners often expect it.", str(path)))

    for folder, detail in {"roms": "ROM/homebrew folder detected.", "saves": "Save folder detected.", "themes": "Theme folder detected."}.items():
        path = root / folder
        if path.exists():
            items.append(CheckItem("good", f"{folder} folder found", detail, str(path)))

    misplaced_boots = [path for path in _safe_walk_files(root) if path.name.lower() == "boot.nds" and path.parent != root]
    for path in misplaced_boots:
        items.append(CheckItem("warning", "boot.nds found in a subfolder", "boot.nds usually belongs at the SD root.", str(path)))

    for path in find_zero_byte_files(root)[:100]:
        items.append(CheckItem("risk", "Zero-byte file", "This file is empty and may be incomplete or corrupted.", path))

    for duplicate in _find_suspicious_duplicates(root):
        items.append(CheckItem("warning", "Suspicious duplicate file", "Multiple setup-like files share this name.", duplicate))

    return items


def check_themes(root: Path) -> ThemeReport:
    candidates = [root / "_nds" / "TWiLightMenu" / "themes", root / "_nds" / "TwilightMenu" / "themes", root / "themes"]
    theme_root = next((path for path in candidates if path.is_dir()), candidates[0])
    report = ThemeReport(theme_root=str(theme_root))
    if not theme_root.exists():
        report.items.append(CheckItem("warning", "Theme folder not found", "No common TWiLight theme folder was found.", str(theme_root)))
        return report

    for folder in sorted(path for path in theme_root.iterdir() if path.is_dir()):
        report.checked_folders += 1
        names = {child.name.lower(): child for child in folder.iterdir() if child.is_file()}
        missing = [asset for asset in THEME_ASSETS if asset not in names]
        if missing:
            report.items.append(CheckItem("warning", f"Theme assets missing in {folder.name}", ", ".join(missing), str(folder)))
        else:
            report.items.append(CheckItem("good", f"Theme structure looks complete: {folder.name}", "Common theme assets are present.", str(folder)))

        # PNG dimensions are read directly from the header to keep dependencies minimal.
        for image_path in [path for path in folder.iterdir() if path.suffix.lower() in {".png", ".bmp"}]:
            try:
                dimensions = read_png_dimensions(image_path) if image_path.suffix.lower() == ".png" else None
                if dimensions:
                    width, height = dimensions
                    if width > 1024 or height > 1024:
                        report.items.append(CheckItem("warning", "Theme image is unusually large", f"{width}x{height}", str(image_path)))
            except OSError:
                report.items.append(CheckItem("risk", "Theme image could not be opened", "The image may be broken.", str(image_path)))
    return report


def match_saves(root: Path) -> SaveMatchReport:
    roms = [path for path in _safe_walk_files(root) if _looks_like_rom(path, root)]
    saves = [path for path in _safe_walk_files(root) if path.suffix.lower() in SAVE_TYPES]
    rom_stems = {_normalized_stem(path): path for path in roms}
    save_stems = {_normalized_stem(path): path for path in saves}
    report = SaveMatchReport(rom_count=len(roms), save_count=len(saves))
    report.roms_without_saves = sorted(str(path) for stem, path in rom_stems.items() if stem not in save_stems)
    report.saves_without_roms = sorted(str(path) for stem, path in save_stems.items() if stem not in rom_stems)
    report.duplicate_rom_names = _find_duplicate_rom_names(roms)
    for save in saves:
        size = save.stat().st_size
        if size == 0 or size % 512 != 0:
            report.suspicious_saves.append(str(save))
    return report


def suggest_organization(root: Path) -> list[OrganizerSuggestion]:
    suggestions: list[OrganizerSuggestion] = []
    if not root.exists():
        return suggestions
    folder_map = {
        ".nds": "roms/nds",
        ".sav": "saves",
        ".dsv": "saves",
        ".png": "_nds/TWiLightMenu/themes or screenshots",
        ".bmp": "_nds/TWiLightMenu/themes",
        ".ini": "_nds or app-specific config folders",
        ".json": "config or reports",
        ".txt": "docs or reports",
    }
    for path in _safe_walk_files(root):
        suffix = path.suffix.lower()
        if suffix not in KNOWN_TYPES:
            continue
        relative_parent = path.parent.relative_to(root) if path.parent != root else Path(".")
        suggested = folder_map.get(suffix, "organized folder")
        if path.parent == root and suffix not in {".nds", ".txt"}:
            suggestions.append(OrganizerSuggestion(str(path), suffix, suggested, "This file type is usually easier to manage outside the SD root."))
        elif path.name.lower() == "boot.nds" and path.parent != root:
            suggestions.append(OrganizerSuggestion(str(path), suffix, "SD card root", "boot.nds usually belongs directly on the SD root."))
        elif suffix == ".nds" and "private" in {part.lower() for part in path.parts}:
            suggestions.append(OrganizerSuggestion(str(path), suffix, "roms/nds or apps", "NDS apps and games usually should not live in private system folders."))
        elif suffix in SAVE_TYPES and "save" not in str(relative_parent).lower():
            suggestions.append(OrganizerSuggestion(str(path), suffix, "saves", "Save files are easier to match when grouped predictably."))
    return suggestions


def create_backup(
    root: str | Path,
    output_dir: str | Path,
    *,
    full: bool = True,
    compress: bool = False,
    progress: ProgressCallback | None = None,
) -> Path:
    sd_root = Path(root).expanduser().resolve()
    destination_root = Path(output_dir).expanduser().resolve()
    if not sd_root.exists() or not sd_root.is_dir():
        raise FileNotFoundError(f"SD root not found: {sd_root}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = destination_root / "DSiForge_Backups" / timestamp
    if backup_dir.exists():
        raise FileExistsError(f"Backup already exists and will not be overwritten: {backup_dir}")
    backup_dir.mkdir(parents=True, exist_ok=False)

    names = [path.name for path in sd_root.iterdir()] if full else ["boot.nds", "_nds", "roms", "saves", "private", "hiya", "hiya.dsi"]
    planned_files = _collect_backup_files(sd_root, names)
    total = max(len(planned_files), 1)
    copied = 0
    manifest: list[str] = []

    for name in names:
        source = sd_root / name
        if not source.exists():
            continue
        if source.is_dir():
            for file_path in _safe_walk_files(source):
                relative = file_path.relative_to(sd_root)
                destination = backup_dir / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, destination)
                copied += 1
                if progress:
                    progress(copied, total, str(relative))
        else:
            destination = backup_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied += 1
            if progress:
                progress(copied, total, name)
        manifest.append(name)

    (backup_dir / "DSiForge-backup-manifest.txt").write_text(
        "DSiForge backup manifest\n"
        f"Source: {sd_root}\n"
        f"Created: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Mode: {'full SD card folder' if full else 'important setup files'}\n"
        "Copied top-level items:\n"
        + "\n".join(f"- {name}" for name in manifest)
        + "\n",
        encoding="utf-8",
    )

    if not compress:
        return backup_dir

    zip_path = backup_dir.with_suffix(".zip")
    if zip_path.exists():
        raise FileExistsError(f"Backup archive already exists and will not be overwritten: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in _safe_walk_files(backup_dir):
            archive.write(file_path, file_path.relative_to(backup_dir.parent))
    return zip_path


def export_report(report: ScanReport, txt_path: str | Path | None = None, json_path: str | Path | None = None) -> None:
    if txt_path:
        Path(txt_path).expanduser().write_text(report.to_text(), encoding="utf-8")
    if json_path:
        Path(json_path).expanduser().write_text(report.to_json(), encoding="utf-8")


def report_with_backup(report: ScanReport, backup_location: str | Path) -> ScanReport:
    report.backup_location = str(backup_location)
    return report


def suggest_fix_steps(report: ScanReport) -> list[str]:
    steps: list[str] = []
    if not report.summary.looks_like_dsi_sd:
        steps.append("- Confirm you selected the SD card root, not a subfolder.")
    if any(item.title == "boot.nds missing at root" for item in report.setup_items):
        steps.append("- Place the correct open-source boot.nds from the official TWiLight Menu++ release at the SD root.")
    if any(item.title == "_nds folder missing" for item in report.setup_items):
        steps.append("- Reinstall or re-copy the official TWiLight Menu++ _nds folder.")
    if report.save_report.saves_without_roms:
        steps.append("- Keep unmatched saves backed up before reorganizing ROM folders.")
    if report.save_report.duplicate_rom_names:
        steps.append("- Rename or separate duplicate ROM filenames so save matching remains predictable.")
    if report.empty_folders:
        steps.append("- Review empty folders before removing anything manually.")
    if report.theme_report.items:
        steps.append("- Review theme warnings and compare the theme folder with TWiLight Menu++ theme documentation.")
    if not steps:
        steps.append("- Make a backup before changing anything.")
    steps.append("- DSiForge checks are read-only and backups do not modify the original SD card.")
    return steps


def find_empty_folders(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path) for path in root.rglob("*") if path.is_dir() and not any(path.iterdir()))


def find_zero_byte_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path) for path in _safe_walk_files(root) if path.stat().st_size == 0)


def verify_hashes(root: Path, critical_hashes: dict[str, str]) -> dict[str, str]:
    results: dict[str, str] = {}
    for relative, expected in critical_hashes.items():
        path = root / relative
        if not path.exists():
            results[str(path)] = "MISSING"
            continue
        actual = sha256_file(path)
        results[str(path)] = "OK" if actual.lower() == expected.lower() else f"MISMATCH expected {expected}, got {actual}"
    return results


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def _format_items(items: Iterable[CheckItem], empty: str) -> list[str]:
    item_list = list(items)
    if not item_list:
        return [f"- {empty}"]
    lines = []
    for item in item_list:
        suffix = f" ({item.path})" if item.path else ""
        lines.append(f"- {item.title}: {item.detail}{suffix}")
        if item.suggestion:
            lines.append(f"  Suggested fix: {item.suggestion}")
    return lines


def _safe_walk_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return (path for path in root.rglob("*") if path.is_file())


def _looks_like_rom(path: Path, root: Path) -> bool:
    if path.suffix.lower() != ".nds":
        return False
    relative_parts = {part.lower() for part in path.relative_to(root).parts}
    if path.name.lower() == "boot.nds" or "_nds" in relative_parts:
        return False
    return "roms" in relative_parts or path.parent != root


def _normalized_stem(path: Path) -> str:
    stem = path.stem.lower()
    for suffix in (".nds", ".sav"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def _collect_backup_files(root: Path, names: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in names:
        source = root / name
        if source.is_file():
            files.append(source)
        elif source.is_dir():
            files.extend(_safe_walk_files(source))
    return files


def _find_suspicious_duplicates(root: Path) -> list[str]:
    watched = {"boot.nds", "settings.ini", "theme.ini"}
    by_name: dict[str, list[Path]] = {}
    for path in _safe_walk_files(root):
        name = path.name.lower()
        if name in watched:
            by_name.setdefault(name, []).append(path)
    duplicates: list[str] = []
    for paths in by_name.values():
        if len(paths) > 1:
            duplicates.extend(str(path) for path in paths)
    return sorted(duplicates)


def _find_duplicate_rom_names(roms: list[Path]) -> list[str]:
    by_name: dict[str, list[Path]] = {}
    for rom in roms:
        by_name.setdefault(rom.name.lower(), []).append(rom)
    duplicates: list[str] = []
    for paths in by_name.values():
        if len(paths) > 1:
            duplicates.extend(str(path) for path in paths)
    return sorted(duplicates)
