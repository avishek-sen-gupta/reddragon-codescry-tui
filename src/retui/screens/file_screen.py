"""FileScreen — source viewer with filtered symbols and integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, RichLog, Static

from retui.facade.types import SurveyBundle
from retui.session.config import AppConfig, RepoConfig
from retui.widgets.integration_table import IntegrationTable
from retui.widgets.status_bar import StatusBar
from retui.widgets.symbol_table import SymbolTable


class FileScreen(Screen):
    """Displays source code with syntax highlighting + file-specific symbols and signals."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(
        self,
        config: AppConfig,
        repo: RepoConfig,
        bundle: SurveyBundle | None,
        file_path: str,
    ) -> None:
        super().__init__()
        self.config = config
        self.repo = repo
        self.bundle = bundle
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        with Horizontal(id="file-main"):
            with Vertical(id="source-panel", classes="panel"):
                yield Static(
                    f"[bold #7dcfff]{self._short_path()}[/]", classes="panel-title"
                )
                yield RichLog(id="source-viewer", highlight=True, markup=True)
            with Vertical(id="file-right"):
                with Vertical(id="file-symbols-panel", classes="panel"):
                    yield Static("[bold #7dcfff]Symbols[/]", classes="panel-title")
                    yield SymbolTable(id="file-symbol-table")
                with Vertical(id="file-integrations-panel", classes="panel"):
                    yield Static(
                        "[bold #7dcfff]Integration Signals[/]", classes="panel-title"
                    )
                    yield IntegrationTable(id="file-integration-table")
        yield StatusBar()

    def on_mount(self) -> None:
        self._update_breadcrumb()
        self._show_loading()
        self._load_file()

    def _short_path(self) -> str:
        return (
            self.file_path.rsplit("/", 1)[-1]
            if "/" in self.file_path
            else self.file_path
        )

    def _update_breadcrumb(self) -> None:
        bar = self.query_one(StatusBar)
        bar.breadcrumb = ["Dashboard", self.repo.name, self._short_path()]
        bar.hints = [("Esc", "Back"), ("Enter", "Open Function"), ("q", "Quit")]

    def _show_loading(self) -> None:
        viewer = self.query_one("#source-viewer", RichLog)
        viewer.write("[italic #2ac3de]Loading source...[/]")

    @work(thread=True, description="Loading file...")
    def _load_file(self) -> None:
        """Load source and table data in a background thread."""
        source_data = self._read_source()
        symbols = self.bundle.symbols_for_file(self.file_path) if self.bundle else []
        signals = self.bundle.signals_for_file(self.file_path) if self.bundle else []
        self.app.call_from_thread(self._populate_ui, source_data, symbols, signals)

    def _read_source(self) -> dict:
        """Read file content from disk (runs in background thread)."""
        repo_root = Path(self.repo.path).expanduser().resolve()
        full_path = repo_root / self.file_path

        if not full_path.exists():
            return {"error": f"File not found: {full_path}"}

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": f"Error reading file: {e}"}

        return {"content": content, "ext": full_path.suffix.lower()}

    def _populate_ui(self, source_data: dict, symbols: list, signals: list) -> None:
        """Update all UI widgets on the main thread."""
        viewer = self.query_one("#source-viewer", RichLog)
        viewer.clear()

        if "error" in source_data:
            viewer.write(f"[#f7768e]{source_data['error']}[/]")
        else:
            lang_map = {
                ".py": "python",
                ".java": "java",
                ".js": "javascript",
                ".ts": "typescript",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".php": "php",
                ".c": "c",
                ".cpp": "cpp",
                ".cs": "csharp",
                ".kt": "kotlin",
                ".scala": "scala",
            }
            from rich.syntax import Syntax

            syntax = Syntax(
                source_data["content"],
                lexer=lang_map.get(source_data["ext"], "text"),
                theme="monokai",
                line_numbers=True,
            )
            viewer.write(syntax)

        # Tables
        if symbols:
            sym_table = self.query_one("#file-symbol-table", SymbolTable)
            sym_table.populate(symbols)
        if signals:
            int_table = self.query_one("#file-integration-table", IntegrationTable)
            int_table.populate(signals)

    @on(DataTable.RowSelected, "#file-symbol-table")
    def on_symbol_selected(self, event: DataTable.RowSelected) -> None:
        """Open FunctionScreen when a function/method symbol is selected."""
        sym_table = self.query_one("#file-symbol-table", SymbolTable)
        row_key = str(event.row_key.value) if event.row_key else ""
        sym_info = sym_table.get_symbol_by_key(row_key)
        if not sym_info:
            return

        kind = sym_info["kind"].lower()
        if kind in ("function", "method", "def", "member"):
            from retui.screens.function_screen import FunctionScreen

            self.app.push_screen(
                FunctionScreen(
                    config=self.config,
                    repo=self.repo,
                    bundle=self.bundle,
                    file_path=self.file_path,
                    symbol_info=sym_info,
                )
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
