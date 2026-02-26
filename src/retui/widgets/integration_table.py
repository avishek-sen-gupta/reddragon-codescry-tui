"""DataTable widget for displaying integration signals."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import DataTable


def _confidence_markup(confidence: str) -> str:
    c = confidence.upper()
    if c == "HIGH":
        return "[#9ece6a]HIGH[/]"
    elif c == "MEDIUM":
        return "[#e0af68]MEDIUM[/]"
    return "[#f7768e]LOW[/]"


def _direction_markup(direction: str) -> str:
    d = direction.upper()
    if d == "INWARD":
        return "[#9ece6a]INWARD[/]"
    elif d == "OUTWARD":
        return "[#f7768e]OUTWARD[/]"
    return "[#e0af68]AMBIGUOUS[/]"


class IntegrationTable(DataTable):
    """Displays integration signals with confidence/direction coloring."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(cursor_type="row", **kwargs)

    def on_mount(self) -> None:
        self.add_columns(
            "File", "Line", "Type", "Confidence", "Direction", "Matched Line"
        )

    def populate(self, signals: list[Any]) -> None:
        """Fill the table with IntegrationSignal objects."""
        self.clear()
        for signal in signals:
            file_path = signal.match.file_path
            # Show just the filename for brevity
            short_path = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
            self.add_row(
                short_path,
                str(signal.match.line_number),
                (
                    signal.integration_type.value
                    if hasattr(signal.integration_type, "value")
                    else str(signal.integration_type)
                ),
                _confidence_markup(
                    signal.confidence.value
                    if hasattr(signal.confidence, "value")
                    else str(signal.confidence)
                ),
                _direction_markup(
                    signal.direction.value
                    if hasattr(signal.direction, "value")
                    else str(signal.direction)
                ),
                signal.match.line_content.strip() if signal.match.line_content else "",
                key=f"{file_path}:{signal.match.line_number}",
            )
