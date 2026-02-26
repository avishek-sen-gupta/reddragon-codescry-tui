"""Dataflow viewer with toggleable table and visual graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, RichLog, Static


class DataflowViewer(Widget):
    """Displays def-use chains as a table or visual graph, toggled with 'd'."""

    DEFAULT_CSS = """
    DataflowViewer {
        height: 1fr;
    }
    #df-table {
        height: 1fr;
    }
    #df-graph {
        height: 1fr;
    }
    #df-mode-label {
        height: 1;
        dock: bottom;
        background: #414868;
        color: #565f89;
        padding: 0 1;
    }
    """

    show_graph: reactive[bool] = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._dataflow_result: Any = None

    def compose(self) -> ComposeResult:
        yield DataTable(id="df-table", cursor_type="row")
        yield RichLog(id="df-graph", highlight=False, markup=True)
        yield Static("[italic]Press 'd' to toggle table/graph[/]", id="df-mode-label")

    def on_mount(self) -> None:
        table = self.query_one("#df-table", DataTable)
        table.add_columns("Def Variable", "Def Block", "Def Idx", "Use Variable", "Use Block", "Use Idx")
        self._sync_visibility()

    def watch_show_graph(self, value: bool) -> None:
        self._sync_visibility()

    def _sync_visibility(self) -> None:
        try:
            self.query_one("#df-table").display = not self.show_graph
            self.query_one("#df-graph").display = self.show_graph
            mode = "graph" if self.show_graph else "table"
            self.query_one("#df-mode-label", Static).update(
                f"[italic]Press 'd' to toggle — viewing [bold #7dcfff]{mode}[/bold #7dcfff][/]"
            )
        except Exception as e:
            graph = self.query_one("#df-graph", RichLog)
            graph.write(f"[#f7768e]Error toggling view: {e}[/]")

    def toggle_view(self) -> None:
        self.show_graph = not self.show_graph

    def populate(self, dataflow_result: Any) -> None:
        """Fill both table and graph from a DataflowResult."""
        self._dataflow_result = dataflow_result
        self._populate_table(dataflow_result)
        self._populate_graph(dataflow_result)

    def _populate_table(self, result: Any) -> None:
        table = self.query_one("#df-table", DataTable)
        table.clear()
        if not result or not hasattr(result, "def_use_chains"):
            return
        for link in result.def_use_chains:
            table.add_row(
                link.definition.variable,
                link.definition.block_label,
                str(link.definition.instruction_index),
                link.use.variable,
                link.use.block_label,
                str(link.use.instruction_index),
            )

    def _populate_graph(self, result: Any) -> None:
        graph = self.query_one("#df-graph", RichLog)
        graph.clear()
        if not result:
            graph.write("[#565f89]No dataflow data[/]")
            return

        # Section 1: Def-Use chain visualisation
        if hasattr(result, "def_use_chains") and result.def_use_chains:
            graph.write(Text("Def-Use Chains", style="bold #7dcfff underline"))
            graph.write("")

            # Group chains by definition variable
            chains_by_var: dict[str, list] = defaultdict(list)
            for link in result.def_use_chains:
                chains_by_var[link.definition.variable].append(link)

            for var, links in chains_by_var.items():
                defn = links[0].definition
                opcode = ""
                if hasattr(defn.instruction, "opcode"):
                    opcode = defn.instruction.opcode.value if hasattr(defn.instruction.opcode, "value") else str(defn.instruction.opcode)

                # Definition header
                header = Text()
                header.append(f"  {var}", style="bold #9ece6a")
                header.append(f"  defined in ", style="#565f89")
                header.append(defn.block_label, style="#7dcfff")
                header.append(f":{defn.instruction_index}", style="#565f89")
                if opcode:
                    header.append(f"  ({opcode})", style="#e0af68")
                graph.write(header)

                # Use arrows
                for link in links:
                    use = link.use
                    use_opcode = ""
                    if hasattr(use.instruction, "opcode"):
                        use_opcode = use.instruction.opcode.value if hasattr(use.instruction.opcode, "value") else str(use.instruction.opcode)

                    arrow = Text()
                    arrow.append("    └──▸ ", style="#7dcfff")
                    arrow.append(use.variable, style="#bb9af7")
                    arrow.append(" in ", style="#565f89")
                    arrow.append(use.block_label, style="#7dcfff")
                    arrow.append(f":{use.instruction_index}", style="#565f89")
                    if use_opcode:
                        arrow.append(f"  ({use_opcode})", style="#e0af68")
                    graph.write(arrow)

                graph.write("")

        # Section 2: Dependency graph
        if hasattr(result, "dependency_graph") and result.dependency_graph:
            graph.write(Text("Variable Dependencies", style="bold #7dcfff underline"))
            graph.write("")

            for var, deps in sorted(result.dependency_graph.items()):
                line = Text()
                line.append(f"  {var}", style="bold #bb9af7")
                if deps:
                    line.append(" ← ", style="#7dcfff")
                    dep_parts = []
                    for d in sorted(deps):
                        dep_parts.append(d)
                    line.append(", ".join(dep_parts), style="#c0caf5")
                else:
                    line.append("  (root — no dependencies)", style="#565f89")
                graph.write(line)

        # Section 3: Block reaching definitions summary
        if hasattr(result, "block_facts") and result.block_facts:
            graph.write("")
            graph.write(Text("Reaching Definitions", style="bold #7dcfff underline"))
            graph.write("")

            for block_label, facts in result.block_facts.items():
                reach_in_vars = sorted({d.variable for d in facts.reach_in}) if facts.reach_in else []
                reach_out_vars = sorted({d.variable for d in facts.reach_out}) if facts.reach_out else []

                if not reach_in_vars and not reach_out_vars:
                    continue

                block_line = Text()
                block_line.append(f"  [{block_label}]", style="bold #7dcfff")
                graph.write(block_line)

                if reach_in_vars:
                    in_line = Text()
                    in_line.append("    reach_in:  ", style="#565f89")
                    in_line.append(", ".join(reach_in_vars), style="#9ece6a")
                    graph.write(in_line)

                if reach_out_vars:
                    out_line = Text()
                    out_line.append("    reach_out: ", style="#565f89")
                    out_line.append(", ".join(reach_out_vars), style="#f7768e")
                    graph.write(out_line)
