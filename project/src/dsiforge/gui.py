from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .core import create_backup, export_report, report_with_backup, scan_sd
from .state import add_backup_record, format_backup_history, load_state, remember_report, save_state, state_dir, state_path, update_settings


class DSiForgeWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DSiForge")
        self.resize(1240, 780)
        self.state = load_state()
        self.sd_root: Path | None = Path(self.state.settings.last_sd_path) if self.state.settings.last_sd_path else None
        self.report = None
        self.last_backup: Path | None = None

        shell = QWidget()
        shell.setObjectName("AppShell")
        root_layout = QHBoxLayout(shell)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(224)
        for name in ["Dashboard", "Scan", "Backup", "Save/ROM Checker", "Theme Tools", "Reports", "Settings"]:
            QListWidgetItem(name, self.sidebar)
        self.sidebar.currentRowChanged.connect(self._switch_page)

        self.stack = QStackedWidget()
        self.scan_progress = QProgressBar()
        self.backup_progress = QProgressBar()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("Status")
        self.logs = self._report_box()
        self.logs.setMaximumHeight(150)

        self.dashboard_text = self._report_box()
        self.scan_text = self._report_box()
        self.backup_text = self._report_box()
        self.theme_text = self._report_box()
        self.save_text = self._report_box()
        self.reports_text = self._report_box()
        self.settings_text = self._report_box()
        self.compress_backup = QCheckBox("Create .zip archive after backup")
        self.compress_backup.setChecked(self.state.settings.compress_backups_by_default)
        self.auto_report = QCheckBox("Auto-generate reports after scan")
        self.auto_report.setChecked(self.state.settings.auto_report_after_scan)
        self.interface_choice = QComboBox()
        self.interface_choice.addItems(["ask", "terminal", "gui"])
        self.interface_choice.setCurrentText(self.state.settings.preferred_interface)

        self.stack.addWidget(self._dashboard_page())
        self.stack.addWidget(self._scan_page())
        self.stack.addWidget(self._backup_page())
        self.stack.addWidget(self._text_page("Save/ROM Checker", self.save_text))
        self.stack.addWidget(self._text_page("Theme Tools", self.theme_text))
        self.stack.addWidget(self._reports_page())
        self.stack.addWidget(self._settings_page())

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self.sidebar.setCurrentRow(0)
        self._apply_theme()
        self._show_welcome()

    def _dashboard_page(self) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("DSiForge")
        title.setObjectName("Hero")
        subtitle = QLabel("Safe DSi homebrew setup assistant and SD card manager")
        subtitle.setObjectName("Subtitle")

        actions = QHBoxLayout()
        choose = QPushButton("Choose SD Card Root")
        choose.clicked.connect(self.choose_sd)
        scan = QPushButton("Run Scan")
        scan.clicked.connect(self.run_scan)
        backup = QPushButton("Backup SD Card")
        backup.clicked.connect(self.make_backup)
        wizard = QPushButton("First-run Wizard")
        wizard.clicked.connect(self.first_run_wizard)
        actions.addWidget(choose)
        actions.addWidget(scan)
        actions.addWidget(backup)
        actions.addWidget(wizard)
        actions.addStretch(1)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(actions)
        layout.addWidget(self._panel(self.dashboard_text), 1)
        layout.addWidget(self.status_label)
        layout.addWidget(self._log_panel())
        return page

    def _scan_page(self) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Scan")
        title.setObjectName("PageTitle")
        run = QPushButton("Run Comprehensive Scan")
        run.clicked.connect(self.run_scan)
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        layout.addWidget(title)
        layout.addWidget(run, alignment=Qt.AlignLeft)
        layout.addWidget(self.scan_progress)
        layout.addWidget(self._panel(self.scan_text), 1)
        return page

    def _backup_page(self) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Backup")
        title.setObjectName("PageTitle")
        create = QPushButton("Backup SD Card")
        create.clicked.connect(self.make_backup)
        default_backup = QPushButton("Use Default Backup Folder")
        default_backup.clicked.connect(self.make_backup_to_default)
        self.backup_progress.setRange(0, 100)
        self.backup_progress.setValue(0)
        layout.addWidget(title)
        actions = QHBoxLayout()
        actions.addWidget(create)
        actions.addWidget(default_backup)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(self.compress_backup)
        layout.addWidget(self.backup_progress)
        layout.addWidget(self._panel(self.backup_text), 1)
        return page

    def _settings_page(self) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Settings")
        title.setObjectName("PageTitle")

        choose_backup = QPushButton("Choose Default Backup Folder")
        choose_backup.clicked.connect(self.choose_default_backup)
        save_preferences = QPushButton("Save Preferences")
        save_preferences.clicked.connect(self.save_preferences)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Preferred interface:"))
        controls.addWidget(self.interface_choice)
        controls.addWidget(choose_backup)
        controls.addWidget(save_preferences)
        controls.addStretch(1)

        layout.addWidget(title)
        layout.addLayout(controls)
        layout.addWidget(self.auto_report)
        layout.addWidget(self._panel(self.settings_text), 1)
        return page

    def _reports_page(self) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Reports")
        title.setObjectName("PageTitle")
        export_txt = QPushButton("Export TXT")
        export_txt.clicked.connect(lambda: self.export_current("txt"))
        export_json = QPushButton("Export JSON")
        export_json.clicked.connect(lambda: self.export_current("json"))
        actions = QHBoxLayout()
        actions.addWidget(export_txt)
        actions.addWidget(export_json)
        actions.addStretch(1)
        layout.addWidget(title)
        layout.addLayout(actions)
        layout.addWidget(self._panel(self.reports_text), 1)
        return page

    def _text_page(self, title_text: str, text_box: QTextEdit) -> QWidget:
        page = self._page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel(title_text)
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        layout.addWidget(self._panel(text_box), 1)
        return page

    def _page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("Page")
        return page

    def _panel(self, child: QWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("GlassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.addWidget(child)
        return panel

    def _log_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("GlassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 14)
        title = QLabel("Real-time logs")
        title.setObjectName("SmallTitle")
        layout.addWidget(title)
        layout.addWidget(self.logs)
        return panel

    def _report_box(self) -> QTextEdit:
        box = QTextEdit()
        box.setReadOnly(True)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return box

    def choose_sd(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose SD Card Root")
        if folder:
            self.sd_root = Path(folder)
            update_settings(last_sd_path=str(self.sd_root))
            self._log(f"Selected SD root: {self.sd_root}", "good")
            self.dashboard_text.setPlainText(f"Selected SD root:\n{self.sd_root}\n\nRun Scan when ready.")

    def run_scan(self) -> None:
        if not self.sd_root:
            self.choose_sd()
        if not self.sd_root:
            return
        self.scan_progress.setValue(8)
        self._notify("Scan started", "Checking SD card structure...", "info")
        QApplication.processEvents()

        self.scan_progress.setValue(35)
        self.report = scan_sd(self.sd_root)
        QApplication.processEvents()

        self.scan_progress.setValue(78)
        self._refresh_report_views()
        self._auto_export_report()
        self.scan_progress.setValue(100)
        risk_count = len(self.report.missing) + len(self.report.risky)
        if risk_count:
            self._notify("Scan completed with warnings", f"{risk_count} issue(s) need review.", "warning")
        else:
            self._notify("Scan completed", "No critical issues found.", "good")

    def make_backup(self) -> None:
        if not self.sd_root:
            self.choose_sd()
        if not self.sd_root:
            return
        default_dir = self.state.settings.default_backup_dir
        output = QFileDialog.getExistingDirectory(self, "Choose Backup Destination", default_dir)
        if not output:
            return
        self._make_backup_to(Path(output))

    def make_backup_to_default(self) -> None:
        default_dir = self.state.settings.default_backup_dir
        if not default_dir:
            QMessageBox.information(self, "No default backup folder", "Choose a default backup folder in Settings first.")
            return
        self._make_backup_to(Path(default_dir))

    def _make_backup_to(self, output: Path) -> None:
        if not self.sd_root:
            self.choose_sd()
        if not self.sd_root:
            return

        self.backup_progress.setValue(0)
        self._notify("Backup started", "Copying the full SD card folder. Original files are read-only.", "info")

        def progress(done: int, total: int, current: str) -> None:
            percent = int((done / max(total, 1)) * 100)
            self.backup_progress.setValue(min(percent, 100))
            self._log(f"Backed up {done}/{total}: {current}", "info")
            QApplication.processEvents()

        try:
            backup_location = create_backup(self.sd_root, output, full=True, compress=self.compress_backup.isChecked(), progress=progress)
        except Exception as exc:
            self._notify("Backup failed", str(exc), "risk")
            QMessageBox.critical(self, "Backup failed", str(exc))
            return

        self.last_backup = backup_location
        self.backup_progress.setValue(100)
        self.report = report_with_backup(scan_sd(self.sd_root), backup_location)
        add_backup_record(self.sd_root, backup_location, self.report.summary.file_count, zipped=self.compress_backup.isChecked())
        self.state = load_state()
        self._refresh_report_views()
        self.backup_text.setPlainText(
            f"Backup completed successfully.\n\nLocation:\n{backup_location}\n\n"
            "The original SD card folder was not modified. DSiForge never overwrites existing backup folders.\n\n"
            "Recent backups:\n"
            f"{format_backup_history(limit=8)}"
        )
        self._notify("Backup completed", f"Saved to {backup_location}", "good")
        QMessageBox.information(self, "Backup completed", f"Backup saved to:\n{backup_location}")

    def export_current(self, kind: str) -> None:
        if not self.report:
            self.run_scan()
        if not self.report:
            return
        extension = "txt" if kind == "txt" else "json"
        path, _ = QFileDialog.getSaveFileName(self, f"Export {extension.upper()} Report", f"dsiforge-report.{extension}")
        if not path:
            return
        export_report(self.report, txt_path=path if kind == "txt" else None, json_path=path if kind == "json" else None)
        remember_report(txt_path=path if kind == "txt" else None, json_path=path if kind == "json" else None)
        self._notify("Report exported", f"Wrote {path}", "good")
        QMessageBox.information(self, "Report exported", f"Wrote {path}")

    def first_run_wizard(self) -> None:
        QMessageBox.information(
            self,
            "First-run wizard",
            "Step 1: choose your SD card root.\n\nDSiForge will scan it, explain any issues, and then offer to create a backup.",
        )
        self.choose_sd()
        if not self.sd_root:
            return
        self.run_scan()
        if QMessageBox.question(self, "Create backup?", "Step 2: create a safe backup now?") == QMessageBox.Yes:
            self.make_backup()
        self.state.settings.first_run_complete = True
        save_state(self.state)
        QMessageBox.information(self, "Wizard complete", "Your first scan is complete. Review Reports for suggested next steps.")

    def choose_default_backup(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Default Backup Folder", self.state.settings.default_backup_dir)
        if folder:
            self.state = update_settings(default_backup_dir=folder)
            self._refresh_settings_view()
            self._notify("Settings updated", f"Default backup folder set to {folder}", "good")

    def save_preferences(self) -> None:
        self.state = update_settings(
            preferred_interface=self.interface_choice.currentText(),
            auto_report_after_scan=self.auto_report.isChecked(),
            compress_backups_by_default=self.compress_backup.isChecked(),
        )
        self._refresh_settings_view()
        self._notify("Settings saved", "Preferences were written to disk.", "good")

    def _auto_export_report(self) -> None:
        if not self.report or not self.auto_report.isChecked():
            return
        reports_dir = state_dir() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.report.generated_at.replace(":", "-")
        txt_path = reports_dir / f"scan-{stamp}.txt"
        json_path = reports_dir / f"scan-{stamp}.json"
        export_report(self.report, txt_path, json_path)
        remember_report(txt_path, json_path)
        self._log(f"Auto-exported reports to {reports_dir}", "good")

    def _refresh_report_views(self) -> None:
        if not self.report:
            return
        summary = self.report.summary
        self.dashboard_text.setHtml(
            self._html_title("Dashboard")
            + f"""
            <p><b>Selected SD root:</b> {summary.root}</p>
            <p><b>Looks like a DSi SD card:</b> {'Yes' if summary.looks_like_dsi_sd else 'Not sure'}</p>
            <p><b>Files:</b> {summary.file_count} &nbsp; <b>Folders:</b> {summary.folder_count}</p>
            <p><b>ROMs:</b> {summary.rom_count} &nbsp; <b>Saves:</b> {summary.save_count} &nbsp; <b>Config files:</b> {summary.config_count}</p>
            <p><b>Free space:</b> {summary.free_bytes / (1024 ** 3):.2f} GB</p>
            <p><b>Top-level folders:</b> {', '.join(summary.top_level_folders) or 'None'}</p>
            <p class="warn">Safety: checks are read-only. Backups copy files and do not modify the original SD card.</p>
            """
        )
        self.scan_text.setHtml(self._scan_sections_html())
        self.theme_text.setHtml(
            self._html_title("Theme Tools")
            + f"<p><b>Theme root checked:</b> {self.report.theme_report.theme_root}</p>"
            + f"<p><b>Theme folders checked:</b> {self.report.theme_report.checked_folders}</p>"
            + self._theme_preview_html()
            + self._items_html("", self.report.theme_report.items, include_title=False)
        )
        self.save_text.setHtml(self._save_html())
        self.reports_text.setHtml(self._report_sections_html())
        self._refresh_settings_view()

    def _save_html(self) -> str:
        save = self.report.save_report
        sections = [
            self._html_title("Save/ROM Checker"),
            f"<p><b>ROMs found:</b> {save.rom_count}</p>",
            f"<p><b>Saves found:</b> {save.save_count}</p>",
            self._path_list("ROMs with no matching save", save.roms_without_saves, "warn"),
            self._path_list("Saves with no matching ROM", save.saves_without_roms, "warn"),
            self._path_list("Duplicate ROM names", save.duplicate_rom_names, "warn"),
            self._path_list("Suspicious saves", save.suspicious_saves, "risk"),
        ]
        return "\n".join(sections)

    def _scan_sections_html(self) -> str:
        critical = [item for item in self.report.setup_items if item.level in {"missing", "risk"}]
        warnings = [item for item in self.report.setup_items if item.level == "warning"]
        good = [item for item in self.report.setup_items if item.level == "good"]
        return (
            self._html_title("Comprehensive Scan")
            + self._items_html("Critical", critical, include_title=True)
            + self._items_html("Warnings", warnings, include_title=True)
            + self._items_html("Looks Good", good, include_title=True)
        )

    def _report_sections_html(self) -> str:
        return (
            self._html_title("Report Viewer")
            + self._scan_sections_html()
            + self._save_html()
            + self._path_list("Empty folders", self.report.empty_folders, "warn")
            + self._path_list("Zero-byte files", self.report.zero_byte_files, "risk")
            + f"<h2>Suggested Fixes</h2><pre>{self.report.to_text()}</pre>"
        )

    def _theme_preview_html(self) -> str:
        theme_root = Path(self.report.theme_report.theme_root)
        if not theme_root.exists():
            return ""
        image_tags = []
        for image in sorted(theme_root.rglob("*.png"))[:12]:
            image_tags.append(f'<p><b>{image.name}</b><br><img src="{image.as_uri()}" width="192"></p>')
        if not image_tags:
            return '<p class="info">No PNG theme images found to preview.</p>'
        return "<h2>Theme Preview</h2>" + "\n".join(image_tags)

    def _items_html(self, title: str, items: list, include_title: bool = True) -> str:
        parts = [self._html_title(title)] if include_title and title else []
        if not items:
            parts.append('<p class="good">No issues found.</p>')
            return "\n".join(parts)
        for item in items:
            css = {"good": "good", "missing": "risk", "risk": "risk", "warning": "warn"}.get(item.level, "info")
            path = f"<br><small>{item.path}</small>" if item.path else ""
            suggestion = f"<br><em>{item.suggestion}</em>" if item.suggestion else ""
            parts.append(f'<div class="item {css}"><b>{item.title}</b><br>{item.detail}{path}{suggestion}</div>')
        return "\n".join(parts)

    def _path_list(self, title: str, paths: list[str], css: str) -> str:
        if not paths:
            return f'<p><b>{title}:</b> <span class="good">None</span></p>'
        rows = "".join(f"<li>{path}</li>" for path in paths)
        return f'<div class="item {css}"><b>{title}</b><ul>{rows}</ul></div>'

    def _html_title(self, text: str) -> str:
        return f"<h2>{text}</h2>" if text else ""

    def _notify(self, title: str, detail: str, level: str) -> None:
        self.status_label.setProperty("level", level)
        self.status_label.setText(f"{title}: {detail}")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self._log(f"{title}: {detail}", level)

    def _log(self, message: str, level: str = "info") -> None:
        color = {"good": "#67e88f", "warning": "#f7d060", "risk": "#ff6b7a", "info": "#bda7ff"}.get(level, "#bda7ff")
        self.logs.append(f'<span style="color:{color};">[{level.upper()}] {message}</span>')

    def _show_welcome(self) -> None:
        selected = f"\n\nLast SD root:\n{self.sd_root}" if self.sd_root else ""
        self.dashboard_text.setPlainText(
            "Choose your SD card root or run the First-run Wizard to begin.\n\n"
            "DSiForge checks structure, saves, themes, empty folders, duplicates, and common setup mistakes. It only suggests fixes unless you explicitly create a backup or export a report."
            + selected
        )
        self.backup_text.setPlainText("Recent backups:\n" + format_backup_history(limit=8))
        self._refresh_settings_view()

    def _refresh_settings_view(self) -> None:
        self.state = load_state()
        self.settings_text.setHtml(
            self._html_title("Settings")
            + f"""
            <p><b>Settings file:</b> {state_path()}</p>
            <p><b>Last SD root:</b> {self.state.settings.last_sd_path or 'None'}</p>
            <p><b>Default backup folder:</b> {self.state.settings.default_backup_dir or 'None'}</p>
            <p><b>Preferred interface:</b> {self.state.settings.preferred_interface}</p>
            <p><b>Auto report after scan:</b> {self.state.settings.auto_report_after_scan}</p>
            <p><b>Compress backups by default:</b> {self.state.settings.compress_backups_by_default}</p>
            <h2>Backup History</h2>
            <pre>{format_backup_history(limit=10)}</pre>
            <h2>Safety Defaults</h2>
            <ul>
              <li>No automatic deletion</li>
              <li>No automatic file moving</li>
              <li>No piracy tools, ROM downloaders, copyrighted Nintendo files, firmware files, or exploit payloads</li>
              <li>Full-card backups are timestamped under DSiForge_Backups/YYYY-MM-DD_HH-MM-SS/</li>
            </ul>
            """
        )

    def _switch_page(self, row: int) -> None:
        self.stack.setCurrentIndex(max(row, 0))

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget#AppShell, QWidget#Page {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050308, stop:0.45 #12061f, stop:1 #2b0f4d);
                color: #f2ecff;
                font-family: Inter, Segoe UI, Arial, sans-serif;
                font-size: 14px;
            }
            QListWidget#Sidebar {
                background: rgba(10, 5, 18, 225);
                border: 0;
                border-right: 1px solid rgba(174, 127, 255, 60);
                padding: 16px 8px;
                color: #d9c8ff;
            }
            QListWidget::item {
                padding: 13px 14px;
                border-radius: 8px;
                margin: 4px 0;
            }
            QListWidget::item:hover {
                background: rgba(126, 74, 210, 95);
            }
            QListWidget::item:selected {
                background: #6d35c9;
                color: white;
            }
            QFrame#GlassPanel {
                background: rgba(19, 12, 31, 190);
                border: 1px solid rgba(202, 170, 255, 70);
                border-radius: 12px;
            }
            QLabel#Hero {
                font-size: 40px;
                font-weight: 800;
                color: white;
            }
            QLabel#Subtitle {
                color: #c8b4ff;
                font-size: 16px;
                padding-bottom: 12px;
            }
            QLabel#PageTitle {
                font-size: 26px;
                font-weight: 750;
                color: white;
            }
            QLabel#SmallTitle {
                font-size: 13px;
                font-weight: 700;
                color: #d9c8ff;
            }
            QLabel#Status {
                background: rgba(17, 12, 27, 180);
                border: 1px solid rgba(202, 170, 255, 60);
                border-radius: 8px;
                padding: 10px 12px;
                color: #d9c8ff;
            }
            QLabel#Status[level="good"] { color: #67e88f; }
            QLabel#Status[level="warning"] { color: #f7d060; }
            QLabel#Status[level="risk"] { color: #ff6b7a; }
            QPushButton {
                background: #6d35c9;
                color: white;
                border: 1px solid #9c75df;
                padding: 10px 15px;
                border-radius: 9px;
                font-weight: 650;
            }
            QPushButton:hover {
                background: #7e4ad2;
                border-color: #c0a2ff;
            }
            QPushButton:pressed {
                background: #4f238f;
                padding-top: 11px;
                padding-bottom: 9px;
            }
            QTextEdit {
                background: rgba(7, 5, 12, 180);
                border: 0;
                border-radius: 8px;
                padding: 10px;
                color: #efe8ff;
                selection-background-color: #6d35c9;
            }
            QProgressBar {
                background: rgba(7, 5, 12, 180);
                border: 1px solid rgba(202, 170, 255, 75);
                border-radius: 8px;
                height: 18px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d35c9, stop:1 #30d5a5);
                border-radius: 7px;
            }
            QCheckBox {
                color: #e9ddff;
                padding: 4px;
            }
            h2 { color: #ffffff; margin-bottom: 8px; }
            .item {
                border-radius: 8px;
                padding: 9px;
                margin: 7px 0;
            }
            .good { color: #67e88f; }
            .warn { color: #f7d060; }
            .risk { color: #ff6b7a; }
            .info { color: #bda7ff; }
            small { color: #c8b4ff; }
            """
        )


def main() -> int:
    app = QApplication([])
    window = DSiForgeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
