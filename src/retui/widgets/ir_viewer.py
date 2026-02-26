"""RichLog widget for displaying IR instructions with opcode coloring."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import RichLog

# Opcode color categories
_VALUE_OPCODES = {
    "CONST",
    "LOAD_VAR",
    "LOAD_FIELD",
    "LOAD_INDEX",
    "NEW_OBJECT",
    "NEW_ARRAY",
}
_ARITH_OPCODES = {"BINOP", "UNOP"}
_CONTROL_OPCODES = {"BRANCH", "BRANCH_IF", "RETURN", "THROW"}
_STORE_OPCODES = {"STORE_VAR", "STORE_FIELD", "STORE_INDEX"}
_CALL_OPCODES = {"CALL_FUNCTION", "CALL_METHOD", "CALL_UNKNOWN"}
_SPECIAL_OPCODES = {"SYMBOLIC", "LABEL"}


def _opcode_color(opcode_name: str) -> str:
    name = opcode_name.upper()
    if name in _VALUE_OPCODES:
        return "#7dcfff"
    if name in _ARITH_OPCODES:
        return "#bb9af7"
    if name in _CONTROL_OPCODES:
        return "#f7768e"
    if name in _STORE_OPCODES:
        return "#9ece6a"
    if name in _CALL_OPCODES:
        return "#e0af68"
    if name in _SPECIAL_OPCODES:
        return "#ff9e64"
    return "#c0caf5"


class IRViewer(RichLog):
    """Displays IR instructions with color-coded opcodes."""

    def populate(self, instructions: list[Any]) -> None:
        """Write IR instructions with syntax coloring."""
        self.clear()
        for i, inst in enumerate(instructions):
            opcode_name = (
                inst.opcode.value if hasattr(inst.opcode, "value") else str(inst.opcode)
            )
            color = _opcode_color(opcode_name)

            line = Text()
            # Line number
            line.append(f"{i:4d}: ", style="#565f89")

            # Result register
            if inst.result_reg:
                line.append(f"{inst.result_reg}", style="#2ac3de dim")
                line.append(" = ", style="#565f89")

            # Opcode
            line.append(opcode_name, style=f"bold {color}")

            # Operands
            if inst.operands:
                line.append(" ", style="")
                for j, op in enumerate(inst.operands):
                    if j > 0:
                        line.append(", ", style="#565f89")
                    op_str = str(op)
                    if op_str.startswith("%") or op_str.startswith("r"):
                        line.append(op_str, style="#2ac3de dim")
                    else:
                        line.append(op_str, style="#c0caf5")

            # Label
            if inst.label:
                line.append(f" @{inst.label}", style="#ff9e64")

            self.write(line)
