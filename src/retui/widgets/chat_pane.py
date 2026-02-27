"""LLM chat input/output widget for contextual questions."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Input, RichLog, Static

from retui.facade.types import FunctionAnalysis, SurveyBundle
from retui.llm.context import build_system_prompt
from retui.session.config import AppConfig


class ChatPane(Widget):
    """Collapsible right pane for LLM chat."""

    DEFAULT_CSS = """
    ChatPane {
        height: 1fr;
        background: #24283b;
    }
    """

    def __init__(self, config: AppConfig, repo_name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.repo_name = repo_name
        self._messages: list[dict[str, str]] = []
        self._analysis: FunctionAnalysis | None = None
        self._bundle: SurveyBundle | None = None
        self._file_path: str = ""
        self._client = None

    def compose(self) -> ComposeResult:
        yield Static("[bold #7dcfff]Chat[/]", classes="panel-title")
        yield RichLog(id="chat-messages", highlight=False, markup=True, wrap=True)
        yield Input(placeholder="Ask about this code...", id="chat-input")

    def on_mount(self) -> None:
        log = self.query_one("#chat-messages", RichLog)
        log.write("[#565f89]Ask questions about the code you're viewing.[/]")

    def set_analysis_context(
        self,
        analysis: FunctionAnalysis | None,
        bundle: SurveyBundle | None = None,
        file_path: str = "",
    ) -> None:
        """Update the analysis context for system prompt building."""
        self._analysis = analysis
        self._bundle = bundle
        self._file_path = file_path

    def _get_client(self):
        if self._client is None:
            from retui.llm.client import LLMClient

            self._client = LLMClient(self.config.llm)
        return self._client

    @on(Input.Submitted, "#chat-input")
    def on_chat_submit(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return

        user_message = event.value.strip()
        input_widget = self.query_one("#chat-input", Input)
        input_widget.value = ""

        # Show user message
        log = self.query_one("#chat-messages", RichLog)
        log.write(f"\n[#c0caf5 on #24283b]You:[/] {user_message}")

        # Add to message history
        self._messages.append({"role": "user", "content": user_message})

        # Send to LLM
        self._send_to_llm()

    @work(thread=True, description="Querying LLM...")
    def _send_to_llm(self) -> None:
        try:
            client = self._get_client()
            system_prompt = build_system_prompt(
                repo_name=self.repo_name,
                file_path=self._file_path,
                analysis=self._analysis,
                bundle=self._bundle,
            )

            response = client.chat(
                messages=self._messages,
                system_prompt=system_prompt,
            )

            self._messages.append({"role": "assistant", "content": response})
            self.app.call_from_thread(self._show_response, response)
        except Exception as e:
            self.app.call_from_thread(self._show_error, str(e))

    def _show_response(self, response: str) -> None:
        log = self.query_one("#chat-messages", RichLog)
        log.write(f"\n[#9ece6a on #1a1b26]Assistant:[/] {response}")

    def _show_error(self, error: str) -> None:
        log = self.query_one("#chat-messages", RichLog)
        log.write(f"\n[#f7768e]Error: {error}[/]")
