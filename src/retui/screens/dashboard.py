"""DashboardScreen — multi-repo overview with DataTable."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static

from retui.session.config import AppConfig, RepoConfig
from retui.widgets.status_bar import StatusBar


class DashboardScreen(Screen):
    """Lists all configured repos; Enter drills into a repo."""

    BINDINGS = []

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self._selected_repo: RepoConfig | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="dashboard-main"):
            with Vertical(id="repo-list-panel", classes="panel"):
                yield Static("[bold #7dcfff]Repos[/]", classes="panel-title")
                yield DataTable(id="repo-table", cursor_type="row")
            with Vertical(id="summary-panel", classes="panel"):
                yield Static("[bold #7dcfff]Summary[/]", classes="panel-title")
                yield Static("", id="summary-text")
        yield StatusBar()

    def on_mount(self) -> None:
        table = self.query_one("#repo-table", DataTable)
        table.add_columns("Name", "Path", "Languages", "Auto-Survey")
        for repo in self.config.repos:
            exists = Path(repo.path).expanduser().exists()
            path_display = repo.path if exists else f"[#f7768e]{repo.path} (missing)[/]"
            table.add_row(
                repo.name,
                path_display,
                ", ".join(repo.languages) if repo.languages else "-",
                "Yes" if repo.auto_survey else "No",
                key=repo.name,
            )
        self._update_breadcrumb()
        if self.config.repos:
            self._update_summary(self.config.repos[0])

    def _update_breadcrumb(self) -> None:
        bar = self.query_one(StatusBar)
        bar.breadcrumb = ["Dashboard"]
        bar.hints = [("Enter", "Open Repo"), ("q", "Quit")]

    def _update_summary(self, repo: RepoConfig) -> None:
        self._selected_repo = repo
        text = self.query_one("#summary-text", Static)
        lines = [
            f"[bold]{repo.name}[/]",
            f"Path: {repo.path}",
            f"Languages: {', '.join(repo.languages) if repo.languages else 'Not specified'}",
            f"Auto-survey: {'Yes' if repo.auto_survey else 'No'}",
        ]
        text.update("\n".join(lines))

    @on(DataTable.RowHighlighted, "#repo-table")
    def on_repo_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value is not None:
            for repo in self.config.repos:
                if repo.name == event.row_key.value:
                    self._update_summary(repo)
                    break

    @on(DataTable.RowSelected, "#repo-table")
    def on_repo_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key and event.row_key.value is not None:
            for repo in self.config.repos:
                if repo.name == event.row_key.value:
                    from retui.screens.repo_screen import RepoScreen

                    self.app.push_screen(RepoScreen(self.config, repo))
                    break
