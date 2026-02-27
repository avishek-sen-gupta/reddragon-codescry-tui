"""ChatScreen — full-width LLM chat overlay, pushed from FunctionScreen."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen

from retui.facade.types import FunctionAnalysis, SurveyBundle
from retui.session.config import AppConfig
from retui.widgets.chat_pane import ChatPane
from retui.widgets.status_bar import StatusBar


class ChatScreen(Screen):
    """Full-screen chat overlay for LLM-powered contextual Q&A."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(
        self,
        config: AppConfig,
        repo_name: str,
        analysis: FunctionAnalysis | None,
        bundle: SurveyBundle | None,
        file_path: str,
    ) -> None:
        super().__init__()
        self.config = config
        self.repo_name = repo_name
        self._analysis = analysis
        self._bundle = bundle
        self._file_path = file_path

    def compose(self) -> ComposeResult:
        yield ChatPane(
            config=self.config,
            repo_name=self.repo_name,
            id="chat-pane",
        )
        yield StatusBar()

    def on_mount(self) -> None:
        chat = self.query_one("#chat-pane", ChatPane)
        chat.set_analysis_context(self._analysis, self._bundle, self._file_path)

        bar = self.query_one(StatusBar)
        bar.breadcrumb = ["Chat"]
        bar.hints = [
            ("Esc", "Back"),
            ("q", "Quit"),
        ]

    def action_go_back(self) -> None:
        self.app.pop_screen()
