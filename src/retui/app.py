"""Main Textual App for Rev-Eng TUI."""

from __future__ import annotations

from textual.app import App

from retui.facade.analysis import AnalysisFacade
from retui.screens.dashboard import DashboardScreen
from retui.session.config import AppConfig
from retui.session.models import SessionMeta
from retui.session.persistence import SessionManager


class RevEngApp(App):
    """Top-down reverse engineering TUI."""

    TITLE = "Rev-Eng TUI"
    CSS_PATH = "app.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self._facade = AnalysisFacade(embedding_config=config.embedding)
        self._session = SessionManager(config)
        self._session.ensure_dirs()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.config))

    def on_unmount(self) -> None:
        """Save session state on exit."""
        meta = SessionMeta(last_screen="dashboard")
        try:
            screen_name = type(self.screen).__name__
            meta.last_screen = screen_name
        except Exception:
            pass
        self._session.save_meta(meta)
