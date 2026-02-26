"""Widget for displaying rendered CFG images in the terminal."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import RichLog, Static


class CFGViewer(Widget):
    """Displays CFG as rendered image or text fallback."""

    DEFAULT_CSS = """
    CFGViewer {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._dot_source: str = ""
        self._svg_path: Path | None = None

    def compose(self) -> ComposeResult:
        yield RichLog(id="cfg-display", highlight=False, markup=True)

    def display_cfg(self, cfg: Any, dot_source: str = "") -> None:
        """Display CFG as colored text. Press 'o' to open image externally."""
        self._dot_source = dot_source
        display = self.query_one("#cfg-display", RichLog)
        display.clear()

        if cfg:
            self._render_text(display, cfg)
            if dot_source:
                display.write("")
                display.write("[#565f89 italic]Press 'o' to open CFG image in external viewer[/]")
        else:
            display.write("[#565f89]No CFG available[/]")

    def _render_image(self, display: RichLog, dot_source: str) -> None:
        """Attempt to render CFG as an image in the terminal."""
        from retui.rendering.cfg_image import render_cfg_png

        png_path = render_cfg_png(dot_source, scale=1.5)

        try:
            from rich_pixels import Pixels

            pixels = Pixels.from_image_path(str(png_path))
            display.write(pixels)
        except Exception:
            # Fallback: inform user
            display.write("[#2ac3de]CFG image rendered. Press 'o' to open externally.[/]")

    def _render_text(self, display: RichLog, cfg: Any) -> None:
        """Render CFG as colored text."""
        from rich.text import Text

        for label, block in cfg.blocks.items():
            header = Text()
            header.append(f"[{label}]", style="bold #7dcfff")
            preds = ", ".join(block.predecessors) if block.predecessors else "none"
            succs = ", ".join(block.successors) if block.successors else "none"
            header.append(f"  preds=({preds})  succs=[{succs}]", style="#565f89")
            display.write(header)

            for inst in block.instructions:
                line = Text()
                line.append("  ", style="")
                opcode = inst.opcode.value if hasattr(inst.opcode, "value") else str(inst.opcode)
                if inst.result_reg:
                    line.append(f"{inst.result_reg}", style="#2ac3de dim")
                    line.append(" = ", style="#565f89")
                line.append(opcode, style="bold #e0af68")
                if inst.operands:
                    line.append(" " + " ".join(str(o) for o in inst.operands), style="#c0caf5")
                display.write(line)

            display.write("")

    def open_external(self) -> None:
        """Save SVG and open in system viewer."""
        if not self._dot_source:
            return
        from retui.rendering.cfg_image import save_cfg_svg, open_svg_external

        svg_path = Path(tempfile.mktemp(suffix=".svg"))
        save_cfg_svg(self._dot_source, svg_path)
        self._svg_path = svg_path
        open_svg_external(svg_path)
