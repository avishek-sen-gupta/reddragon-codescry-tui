"""Widget for displaying rendered CFG in the terminal."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import RichLog, Static


class CFGViewer(Widget):
    """Displays CFG as colored text with optional external PNG rendering."""

    DEFAULT_CSS = """
    CFGViewer {
        height: 1fr;
    }
    #cfg-status {
        height: 1;
        dock: bottom;
        background: #414868;
        color: #565f89;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cfg: Any = None
        self._mermaid_source: str = ""

    def compose(self) -> ComposeResult:
        yield RichLog(id="cfg-display", highlight=False, markup=True)
        yield Static(
            "[italic]Press 'o' to open CFG as rendered PNG in external viewer[/]",
            id="cfg-status",
        )

    def display_cfg(
        self,
        cfg: Any,
        mermaid_source: str = "",
    ) -> None:
        """Display CFG as colored text. Press 'o' to open rendered SVG externally."""
        self._cfg = cfg
        self._mermaid_source = mermaid_source
        display = self.query_one("#cfg-display", RichLog)
        display.clear()

        if not cfg or not cfg.blocks:
            display.write("[#565f89]No CFG available[/]")
            self._set_status("[#565f89]No CFG data[/]")
            return

        self._render_text(display, cfg)

    def _render_text(self, display: RichLog, cfg: Any) -> None:
        """Render CFG as colored text with block structure and edges."""
        from rich.text import Text

        for label, block in cfg.blocks.items():
            # Block header
            header = Text()
            is_entry = label == cfg.entry
            style = "bold #9ece6a" if is_entry else "bold #7dcfff"
            header.append(f"[{label}]", style=style)
            if is_entry:
                header.append("  (entry)", style="#9ece6a")

            preds = ", ".join(block.predecessors) if block.predecessors else "none"
            succs = ", ".join(block.successors) if block.successors else "none"
            header.append(f"  preds=({preds})", style="#565f89")

            # Color successor labels based on T/F for conditionals
            last = block.instructions[-1] if block.instructions else None
            opcode = ""
            if last:
                opcode = (
                    last.opcode.value
                    if hasattr(last.opcode, "value")
                    else str(last.opcode)
                )

            if opcode == "branch_if" and len(block.successors) == 2:
                header.append("  succs=[", style="#565f89")
                header.append(block.successors[0], style="bold #9ece6a")
                header.append("(T)", style="#9ece6a")
                header.append(", ", style="#565f89")
                header.append(block.successors[1], style="bold #f7768e")
                header.append("(F)", style="#f7768e")
                header.append("]", style="#565f89")
            else:
                header.append(f"  succs=[{succs}]", style="#565f89")

            display.write(header)

            # Instructions
            for inst in block.instructions:
                line = Text()
                line.append("  ", style="")
                opcode_val = (
                    inst.opcode.value
                    if hasattr(inst.opcode, "value")
                    else str(inst.opcode)
                )
                if inst.result_reg:
                    line.append(f"{inst.result_reg}", style="#2ac3de dim")
                    line.append(" = ", style="#565f89")
                line.append(opcode_val, style=self._opcode_style(opcode_val))
                if inst.operands:
                    line.append(
                        " " + " ".join(str(o) for o in inst.operands), style="#c0caf5"
                    )
                if inst.label:
                    line.append(f" {inst.label}", style="#bb9af7")
                display.write(line)

            display.write("")

    def _opcode_style(self, opcode: str) -> str:
        """Return a Rich style string for an opcode."""
        op = opcode.lower()
        if op in (
            "const",
            "load_var",
            "load_field",
            "load_index",
            "new_object",
            "new_array",
        ):
            return "bold #7dcfff"
        if op in ("binop", "unop"):
            return "bold #bb9af7"
        if op in ("branch", "branch_if", "return", "throw"):
            return "bold #f7768e"
        if op in ("store_var", "store_field", "store_index"):
            return "bold #9ece6a"
        if op in ("call_function", "call_method"):
            return "bold #e0af68"
        if op in ("symbolic", "label"):
            return "bold #ff9e64"
        return "#c0caf5"

    def _set_status(self, message: str) -> None:
        """Update the docked status bar text."""
        self.query_one("#cfg-status", Static).update(message)

    def open_external(self) -> None:
        """Render Mermaid to PNG and open in system viewer."""
        if not self._mermaid_source:
            self._set_status("[#f7768e]No CFG data available to render[/]")
            return
        from retui.rendering.cfg_image import mermaid_to_png, open_external

        try:
            self._set_status("[#2ac3de italic]Rendering CFG to PNG...[/]")
            png_path = mermaid_to_png(self._mermaid_source)
            open_external(png_path)
            self._set_status(
                "[italic]Press 'o' to open CFG as rendered PNG in external viewer[/]"
            )
        except Exception as e:
            self._set_status(
                f"[#e0af68]PNG rendering failed ({e}), opening raw Mermaid...[/]"
            )
            mmd_path = Path(tempfile.mktemp(suffix=".mmd"))
            mmd_path.write_text(self._mermaid_source, encoding="utf-8")
            open_external(mmd_path)
