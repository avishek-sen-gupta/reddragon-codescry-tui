"""Breadcrumb navigation status bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar showing navigation breadcrumb."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #414868;
        color: #c0caf5;
        padding: 0 1;
    }
    """

    breadcrumb: reactive[list[str]] = reactive(list, always_update=True)

    def compose(self) -> ComposeResult:
        yield Static("", id="breadcrumb-text")

    def watch_breadcrumb(self, segments: list[str]) -> None:
        label = self.query_one("#breadcrumb-text", Static)
        if segments:
            parts: list[str] = []
            for i, seg in enumerate(segments):
                if i == len(segments) - 1:
                    parts.append(f"[bold #7dcfff]{seg}[/]")
                else:
                    parts.append(f"[#c0caf5]{seg}[/]")
            label.update(" [#565f89]>[/] ".join(parts))
        else:
            label.update("[#565f89](select a repo)[/]")
