"""Widget for step-by-step execution trace replay with IR highlighting."""

from __future__ import annotations

import logging
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, RichLog, Static

logger = logging.getLogger(__name__)

# Opcode color categories (mirrors ir_viewer.py)
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

_HIGHLIGHT_BG = "on #344157"


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


def _format_value(value: Any) -> Text:
    """Format a VM value with appropriate coloring."""
    text = Text()
    if hasattr(value, "__symbolic__") or (
        isinstance(value, dict) and value.get("__symbolic__")
    ):
        name = (
            value.get("name", str(value))
            if isinstance(value, dict)
            else getattr(value, "name", str(value))
        )
        text.append(str(name), style="#ff9e64")
    elif isinstance(value, str):
        text.append(f'"{value}"', style="#9ece6a")
    elif isinstance(value, (int, float)):
        text.append(str(value), style="#e0af68")
    elif value is None:
        text.append("null", style="#565f89")
    else:
        text.append(str(value)[:80], style="#c0caf5")
    return text


def _build_ir_index_map(
    instructions: list[Any],
) -> dict[tuple[str, int], int]:
    """Map (block_label, instruction_index) to flat IR line number.

    Walks the instruction list, tracking which block each instruction
    belongs to and its offset within that block.  LABEL instructions
    start a new block; subsequent non-LABEL instructions are numbered
    sequentially within the block.
    """
    index_map: dict[tuple[str, int], int] = {}
    current_label = ""
    block_ip = 0
    for flat_idx, inst in enumerate(instructions):
        opcode_name = (
            inst.opcode.value if hasattr(inst.opcode, "value") else str(inst.opcode)
        )
        if opcode_name == "LABEL":
            current_label = inst.label or ""
            block_ip = 0
        else:
            index_map[(current_label, block_ip)] = flat_idx
            block_ip += 1
    return index_map


class ExecutionReplayViewer(Widget):
    """Replay execution traces step by step with IR highlighting."""

    DEFAULT_CSS = """
    ExecutionReplayViewer {
        height: 1fr;
    }

    #replay-body {
        height: 1fr;
    }

    #replay-ir {
        width: 2fr;
        overflow-y: auto;
    }

    #replay-state {
        width: 1fr;
        border-left: solid #565f89;
    }

    #replay-frame {
        height: 1fr;
        border-bottom: solid #565f89;
    }

    #replay-heap {
        height: 1fr;
    }

    #replay-controls {
        height: 3;
        dock: bottom;
        align: center middle;
    }

    #replay-controls Button {
        margin: 0 1;
        min-width: 8;
    }

    #step-counter {
        content-align: center middle;
        width: auto;
        margin: 0 2;
        color: #c0caf5;
    }
    """

    current_step: reactive[int] = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._trace = None  # ExecutionTrace
        self._instructions: list[Any] = []
        self._ir_index_map: dict[tuple[str, int], int] = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="replay-body"):
                yield Static(id="replay-ir")
                with Vertical(id="replay-state"):
                    yield RichLog(id="replay-frame", highlight=False, markup=True)
                    yield RichLog(id="replay-heap", highlight=False, markup=True)
            with Horizontal(id="replay-controls"):
                yield Button("Run", id="btn-run", variant="primary")
                yield Button("\u25c0", id="btn-prev")
                yield Button("\u25b6", id="btn-next")
                yield Button("Reset", id="btn-reset")
                yield Static("Step 0/0", id="step-counter")

    def set_trace(self, trace: Any, instructions: list[Any]) -> None:
        """Load a trace and instruction list for replay."""
        self._trace = trace
        self._instructions = instructions
        self._ir_index_map = _build_ir_index_map(instructions)
        self.current_step = 0
        logger.info(
            "Trace loaded: %d steps, %d instructions",
            len(trace.steps) if trace else 0,
            len(instructions),
        )
        self._render_current()

    def step_forward(self) -> None:
        """Advance one step (bounds-checked)."""
        if not self._trace or not self._trace.steps:
            return
        if self.current_step < len(self._trace.steps) - 1:
            self.current_step += 1

    def step_backward(self) -> None:
        """Go back one step (bounds-checked)."""
        if self.current_step > 0:
            self.current_step -= 1

    def reset(self) -> None:
        """Return to step 0."""
        self.current_step = 0

    def run_to_end(self) -> None:
        """Jump to the last step."""
        if self._trace and self._trace.steps:
            self.current_step = len(self._trace.steps) - 1

    def watch_current_step(self, new_value: int) -> None:
        """React to step changes by re-rendering IR and VM state."""
        self._render_current()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_actions = {
            "btn-run": self.run_to_end,
            "btn-prev": self.step_backward,
            "btn-next": self.step_forward,
            "btn-reset": self.reset,
        }
        action = button_actions.get(event.button.id, lambda: None)
        action()

    def _render_current(self) -> None:
        """Render IR listing and VM state for the current step."""
        if not self._trace:
            return
        self._render_ir()
        self._render_frame()
        self._render_heap()
        self._render_step_counter()

    def _render_ir(self) -> None:
        """Render the full IR listing with the current instruction highlighted."""
        ir_static = self.query_one("#replay-ir", Static)

        if not self._instructions:
            ir_static.update("[#565f89]No IR instructions[/]")
            return

        highlight_line = self._current_highlight_line()
        lines: list[Text] = []

        for i, inst in enumerate(self._instructions):
            opcode_name = (
                inst.opcode.value if hasattr(inst.opcode, "value") else str(inst.opcode)
            )
            color = _opcode_color(opcode_name)
            is_highlighted = i == highlight_line

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

            if is_highlighted:
                line.stylize(_HIGHLIGHT_BG)
                line.append("  \u25c0", style="#7aa2f7")

            lines.append(line)

        combined = Text("\n").join(lines)
        ir_static.update(combined)

    def _render_frame(self) -> None:
        """Render the call-stack frame (registers + locals) into the frame pane."""
        display = self.query_one("#replay-frame", RichLog)
        display.clear()

        vm_state = self._current_vm_state()
        if vm_state is None:
            display.write("[#565f89]No frame data[/]")
            return

        if not vm_state.call_stack:
            display.write("[#565f89]No active frame[/]")
            return

        frame = vm_state.call_stack[-1]
        header = Text()
        header.append("Frame: ", style="bold #7dcfff")
        header.append(frame.function_name, style="#7dcfff")
        display.write(header)

        # Registers
        if hasattr(frame, "registers") and frame.registers:
            display.write(Text("Registers", style="bold #565f89"))
            for reg, val in list(frame.registers.items())[:10]:
                reg_line = Text()
                reg_line.append(f"  {reg}", style="#2ac3de dim")
                reg_line.append(" = ", style="#565f89")
                reg_line.append(_format_value(val))
                display.write(reg_line)

        # Local vars
        if hasattr(frame, "local_vars") and frame.local_vars:
            display.write(Text("Locals", style="bold #565f89"))
            for var, val in list(frame.local_vars.items())[:10]:
                var_line = Text()
                var_line.append(f"  {var}", style="#c0caf5")
                var_line.append(" = ", style="#565f89")
                var_line.append(_format_value(val))
                display.write(var_line)

    def _render_heap(self) -> None:
        """Render heap objects and path conditions into the heap pane."""
        display = self.query_one("#replay-heap", RichLog)
        display.clear()

        vm_state = self._current_vm_state()
        if vm_state is None:
            display.write("[#565f89]No heap data[/]")
            return

        # Heap objects with expanded fields
        if vm_state.heap:
            display.write(Text("Heap", style="bold #7dcfff"))
            for addr, obj in vm_state.heap.items():
                heap_line = Text()
                heap_line.append(f"  {addr}", style="#bb9af7")
                type_hint = getattr(obj, "type_hint", None)
                if type_hint:
                    heap_line.append(f" ({type_hint})", style="#565f89")
                display.write(heap_line)

                # Expand object fields if available
                fields = getattr(obj, "fields", {})
                if isinstance(fields, dict):
                    for field_name, field_val in fields.items():
                        field_line = Text()
                        field_line.append(f"    .{field_name}", style="#c0caf5")
                        field_line.append(" = ", style="#565f89")
                        field_line.append(_format_value(field_val))
                        display.write(field_line)
        else:
            display.write("[#565f89]Heap empty[/]")

        # Path conditions
        if vm_state.path_conditions:
            display.write(Text("Conditions", style="bold #7dcfff"))
            for cond in vm_state.path_conditions:
                cond_line = Text()
                cond_line.append(f"  {cond}", style="#9ece6a")
                display.write(cond_line)

    def _render_step_counter(self) -> None:
        """Update the step counter label."""
        counter = self.query_one("#step-counter", Static)
        total = len(self._trace.steps) if self._trace else 0
        counter.update(f"Step {self.current_step}/{total - 1}" if total else "Step 0/0")

    def _current_vm_state(self) -> Any:
        """Get the VMState for the current step."""
        if not self._trace:
            return None
        if self.current_step == 0 and self._trace.initial_state is not None:
            return self._trace.initial_state
        if self._trace.steps and self.current_step <= len(self._trace.steps):
            # Step N shows state after instruction N was executed
            idx = max(0, self.current_step - 1) if self.current_step > 0 else 0
            return self._trace.steps[idx].vm_state
        return None

    def _current_highlight_line(self) -> int:
        """Get the flat IR line number to highlight for the current step."""
        if not self._trace or not self._trace.steps:
            return -1
        idx = min(self.current_step, len(self._trace.steps) - 1)
        step = self._trace.steps[idx]
        return self._ir_index_map.get((step.block_label, step.instruction_index), -1)
