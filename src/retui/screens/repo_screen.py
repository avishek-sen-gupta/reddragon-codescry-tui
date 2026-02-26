"""RepoScreen — single-repo view with file tree, symbols, and integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import LoadingIndicator, Static, Tree

from retui.facade.analysis import AnalysisFacade
from retui.facade.types import SurveyBundle
from retui.session.config import AppConfig, RepoConfig
from retui.widgets.integration_table import IntegrationTable
from retui.widgets.repo_tree import RepoTree
from retui.widgets.status_bar import StatusBar
from retui.widgets.symbol_table import SymbolTable


class RepoScreen(Screen):
    """Displays file tree, symbols, and integration signals for a repo."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, config: AppConfig, repo: RepoConfig) -> None:
        super().__init__()
        self.config = config
        self.repo = repo
        self.bundle: SurveyBundle | None = None

    @property
    def facade(self) -> AnalysisFacade:
        return self.app._facade  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        with Horizontal(id="repo-main"):
            with Vertical(id="file-tree-panel", classes="panel"):
                yield Static("[bold #7dcfff]Files[/]", classes="panel-title")
                yield RepoTree(self.repo.name, id="repo-tree")
            with Vertical(id="repo-right"):
                with Vertical(id="symbols-panel", classes="panel"):
                    yield Static("[bold #7dcfff]Symbols[/]", classes="panel-title")
                    yield SymbolTable(id="symbol-table")
                with Vertical(id="integrations-panel", classes="panel"):
                    yield Static("[bold #7dcfff]Integration Signals[/]", id="integrations-title", classes="panel-title")
                    yield IntegrationTable(id="integration-table")
        yield StatusBar()

    def on_mount(self) -> None:
        self._update_breadcrumb()
        self._show_loading()
        self._run_survey()

    def _update_breadcrumb(self) -> None:
        bar = self.query_one(StatusBar)
        bar.breadcrumb = ["Dashboard", self.repo.name]

    def _show_loading(self) -> None:
        tree = self.query_one("#repo-tree", RepoTree)
        tree.root.add_leaf("[italic #2ac3de]Surveying repository...[/]")
        tree.root.expand()

        sym_table = self.query_one("#symbol-table", SymbolTable)
        sym_table.add_row("[italic #2ac3de]Loading symbols...[/]", "", "", "", "")

        int_table = self.query_one("#integration-table", IntegrationTable)
        int_table.add_row("[italic #2ac3de]Loading...[/]", "", "", "", "", "")

    @work(thread=True, description="Surveying repository...")
    def _run_survey(self) -> None:
        repo_path = str(Path(self.repo.path).expanduser().resolve())
        try:
            self.bundle = self.facade.survey_repo(repo_path, self.repo.languages)
            self.app.call_from_thread(self._populate_widgets)
        except Exception as e:
            self.app.call_from_thread(self._show_survey_error, str(e))

    def _show_survey_error(self, error: str) -> None:
        tree = self.query_one("#repo-tree", RepoTree)
        tree.clear()
        tree.root.add_leaf(f"[#f7768e]Survey failed: {error}[/]")

    def _populate_widgets(self) -> None:
        if not self.bundle:
            return

        # Populate file tree
        tree = self.query_one("#repo-tree", RepoTree)
        file_paths = sorted({e.path for e in self.bundle.all_symbols})
        tree.populate(file_paths)

        # Mark files with integration signals
        signal_files = {s.match.file_path for s in self.bundle.all_signals}
        for fp in signal_files:
            tree.mark_file_has_signals(fp)

        # Populate all symbols
        sym_table = self.query_one("#symbol-table", SymbolTable)
        sym_table.populate(self.bundle.all_symbols)

        # Populate all integrations
        int_table = self.query_one("#integration-table", IntegrationTable)
        int_table.populate(self.bundle.all_signals)

        # Update title with counts
        title = self.query_one("#integrations-title", Static)
        concretised_count = len(self.bundle.concretised_signals)
        if concretised_count > 0:
            title.update(
                f"[bold #7dcfff]Integration Signals[/] "
                f"[#9ece6a]({concretised_count} concretised)[/]"
            )

    @on(Tree.NodeSelected, "#repo-tree")
    def on_file_selected(self, event: Tree.NodeSelected) -> None:
        """When a file (leaf node) is selected, open FileScreen."""
        if not event.node.allow_expand and event.node.data:
            file_path = str(event.node.data)
            from retui.screens.file_screen import FileScreen

            self.app.push_screen(
                FileScreen(self.config, self.repo, self.bundle, file_path)
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()
