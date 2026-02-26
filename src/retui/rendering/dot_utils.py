"""Red Dragon IRCFG to DOT format adapter."""

from __future__ import annotations

from typing import Any


def cfg_to_dot(cfg: Any) -> str:
    """Convert a red-dragon CFG to a Graphviz DOT string.

    Args:
        cfg: interpreter.cfg.CFG instance with .blocks dict and .entry label.

    Returns:
        DOT format string suitable for Graphviz rendering.
    """
    lines = [
        "digraph CFG {",
        '  rankdir=TB;',
        '  node [shape=box, style="filled,rounded", fontname="Courier", fontsize=10, '
        'fillcolor="#24283b", fontcolor="#c0caf5", color="#565f89"];',
        '  edge [color="#7dcfff", fontcolor="#565f89", fontsize=8];',
    ]

    for label, block in cfg.blocks.items():
        # Build node label with instruction summary
        instr_lines: list[str] = []
        for inst in block.instructions[:8]:  # cap at 8 lines per block
            text = str(inst).replace('"', '\\"').replace("<", "\\<").replace(">", "\\>")
            if len(text) > 60:
                text = text[:57] + "..."
            instr_lines.append(text)

        body = "\\l".join(instr_lines)
        if instr_lines:
            body += "\\l"

        # Color entry block differently
        extra = ""
        if label == cfg.entry:
            extra = ', fillcolor="#414868", color="#7dcfff"'

        lines.append(f'  "{label}" [label="{label}:\\n{body}"{extra}];')

        for succ in block.successors:
            lines.append(f'  "{label}" -> "{succ}";')

    lines.append("}")
    return "\n".join(lines)
