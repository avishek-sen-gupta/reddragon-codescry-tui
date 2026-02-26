"""Widget for displaying VM state (heap, stack, path conditions)."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import RichLog, Static


class VMStateViewer(Widget):
    """Displays the VM state tree: heap objects, call stack, path conditions."""

    DEFAULT_CSS = """
    VMStateViewer {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield RichLog(id="vm-display", highlight=False, markup=True)

    def display_state(self, vm_state: Any) -> None:
        """Render the VM state into the log."""
        display = self.query_one("#vm-display", RichLog)
        display.clear()

        if vm_state is None:
            display.write("[#565f89]No VM state available[/]")
            return

        # Heap section
        display.write(Text("Heap Objects", style="bold #7dcfff underline"))
        if vm_state.heap:
            for addr, obj in vm_state.heap.items():
                header = Text()
                header.append(f"  {addr}", style="#bb9af7")
                if hasattr(obj, "type_hint") and obj.type_hint:
                    header.append(f" ({obj.type_hint})", style="#565f89")
                display.write(header)

                if hasattr(obj, "fields"):
                    for field_name, value in obj.fields.items():
                        val_line = Text()
                        val_line.append(f"    .{field_name}", style="#bb9af7")
                        val_line.append(" = ", style="#565f89")
                        val_line.append(self._format_value(value))
                        display.write(val_line)
        else:
            display.write(Text("  (empty)", style="#565f89"))

        display.write("")

        # Call stack section
        display.write(Text("Call Stack", style="bold #7dcfff underline"))
        if vm_state.call_stack:
            for i, frame in enumerate(reversed(vm_state.call_stack)):
                frame_line = Text()
                prefix = "-> " if i == 0 else "   "
                frame_line.append(prefix, style="#565f89")
                frame_line.append(frame.function_name, style="#7dcfff")
                display.write(frame_line)

                # Show registers
                if hasattr(frame, "registers") and frame.registers:
                    for reg, val in list(frame.registers.items())[:10]:
                        reg_line = Text()
                        reg_line.append(f"      {reg}", style="#2ac3de dim")
                        reg_line.append(" = ", style="#565f89")
                        reg_line.append(self._format_value(val))
                        display.write(reg_line)

                # Show local vars
                if hasattr(frame, "local_vars") and frame.local_vars:
                    for var, val in list(frame.local_vars.items())[:10]:
                        var_line = Text()
                        var_line.append(f"      {var}", style="#c0caf5")
                        var_line.append(" = ", style="#565f89")
                        var_line.append(self._format_value(val))
                        display.write(var_line)
        else:
            display.write(Text("  (empty)", style="#565f89"))

        display.write("")

        # Path conditions
        display.write(Text("Path Conditions", style="bold #7dcfff underline"))
        if vm_state.path_conditions:
            for cond in vm_state.path_conditions:
                cond_line = Text()
                cond_line.append("  ", style="")
                cond_line.append(str(cond), style="#9ece6a")
                display.write(cond_line)
        else:
            display.write(Text("  (unconstrained)", style="#565f89"))

    def _format_value(self, value: Any) -> Text:
        """Format a value with appropriate coloring."""
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
