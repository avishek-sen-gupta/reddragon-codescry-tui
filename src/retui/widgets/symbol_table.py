"""DataTable widget for displaying CTags symbols."""

from __future__ import annotations

from typing import Any

from textual.widgets import DataTable


class SymbolTable(DataTable):
    """Displays CTags entries in a sortable table."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(cursor_type="row", **kwargs)
        self._symbol_lookup: dict[str, dict[str, str]] = {}

    def on_mount(self) -> None:
        self.add_columns("Name", "Kind", "Line", "Scope", "Language")

    def populate(self, entries: list[Any]) -> None:
        """Fill the table with CTagsEntry objects."""
        self.clear()
        self._symbol_lookup.clear()
        for entry in entries:
            key = f"{entry.path}:{entry.line}:{entry.name}"
            self._symbol_lookup[key] = {
                "name": entry.name,
                "kind": entry.kind,
                "line": str(entry.line),
                "scope": entry.scope or "-",
                "language": entry.language,
                "path": entry.path,
            }
            self.add_row(
                entry.name,
                entry.kind,
                str(entry.line),
                entry.scope or "-",
                entry.language,
                key=key,
            )

    def get_symbol_by_key(self, key: str) -> dict[str, str] | None:
        """Look up symbol info by row key."""
        return self._symbol_lookup.get(key)
