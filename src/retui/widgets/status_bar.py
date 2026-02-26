"""Breadcrumb navigation status bar with keybinding hints."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar showing navigation breadcrumb and keybinding hints."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #414868;
        color: #c0caf5;
        padding: 0 1;
        layout: horizontal;
    }
    #breadcrumb-text {
        width: auto;
    }
    #keybinding-hints {
        width: 1fr;
        text-align: right;
    }
    """

    breadcrumb: reactive[list[str]] = reactive(list, always_update=True)
    hints: reactive[list[tuple[str, str]]] = reactive(list, always_update=True)

    def compose(self) -> ComposeResult:
        yield Static("", id="breadcrumb-text")
        yield Static("", id="keybinding-hints")

    def watch_breadcrumb(self, segments: list[str]) -> None:
        label = self.query_one("#breadcrumb-text", Static)
        if segments:
            parts: list[str] = [
                (
                    f"[bold #7dcfff]{seg}[/]"
                    if i == len(segments) - 1
                    else f"[#c0caf5]{seg}[/]"
                )
                for i, seg in enumerate(segments)
            ]
            label.update(" [#565f89]>[/] ".join(parts))
        else:
            label.update("[#565f89](select a repo)[/]")

    def watch_hints(self, bindings: list[tuple[str, str]]) -> None:
        label = self.query_one("#keybinding-hints", Static)
        if not bindings:
            label.update("")
            return
        parts = [f"[bold #7dcfff]{key}[/] [#c0caf5]{desc}[/]" for key, desc in bindings]
        label.update("  ".join(parts))
