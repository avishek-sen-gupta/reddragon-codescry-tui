"""FunctionScreen — deep-dive with IR, CFG, VM State, Dataflow tabs + Chat pane."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, TabbedContent, TabPane

from retui.facade.types import FunctionAnalysis, SurveyBundle
from retui.session.config import AppConfig, RepoConfig
from retui.widgets.cfg_viewer import CFGViewer
from retui.widgets.chat_pane import ChatPane
from retui.widgets.dataflow_viewer import DataflowViewer
from retui.widgets.ir_viewer import IRViewer
from retui.widgets.status_bar import StatusBar
from retui.widgets.vm_state_viewer import VMStateViewer


class FunctionScreen(Screen):
    """Displays IR, CFG, VM state, dataflow analysis tabs with LLM chat pane."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("o", "open_cfg_external", "Open CFG"),
        ("d", "toggle_dataflow", "Toggle Dataflow View"),
    ]

    def __init__(
        self,
        config: AppConfig,
        repo: RepoConfig,
        bundle: SurveyBundle | None,
        file_path: str,
        symbol_info: dict[str, str],
    ) -> None:
        super().__init__()
        self.config = config
        self.repo = repo
        self.bundle = bundle
        self.file_path = file_path
        self.symbol_info = symbol_info
        self.analysis: FunctionAnalysis | None = None

    @property
    def facade(self):
        return self.app._facade  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        with Horizontal(id="function-main"):
            with Vertical(id="analysis-panel", classes="panel"):
                with TabbedContent(id="analysis-tabs"):
                    with TabPane("IR", id="ir-tab"):
                        yield IRViewer(id="ir-viewer")
                    with TabPane("CFG", id="cfg-tab"):
                        yield CFGViewer(id="cfg-viewer")
                    with TabPane("VM State", id="vm-tab"):
                        yield VMStateViewer(id="vm-state-viewer")
                    with TabPane("Dataflow", id="dataflow-tab"):
                        yield DataflowViewer(id="dataflow-viewer")
            yield ChatPane(
                config=self.config,
                repo_name=self.repo.name,
                id="chat-pane",
            )
        yield StatusBar()

    def on_mount(self) -> None:
        self._update_breadcrumb()
        self._show_loading()
        self._run_analysis()

    def _show_loading(self) -> None:
        ir_viewer = self.query_one("#ir-viewer", IRViewer)
        ir_viewer.write("[italic #2ac3de]Analyzing function...[/]")

    def _update_breadcrumb(self) -> None:
        bar = self.query_one(StatusBar)
        short_file = self.file_path.rsplit("/", 1)[-1] if "/" in self.file_path else self.file_path
        func_name = self.symbol_info.get("name", "?")
        bar.breadcrumb = ["Dashboard", self.repo.name, short_file, f"{func_name}()"]

    @work(thread=True, description="Analyzing function...")
    def _run_analysis(self) -> None:
        """Extract function source and run red-dragon analysis."""
        source = self._extract_function_source()
        if not source:
            self.app.call_from_thread(self._show_error, "Could not extract function source.")
            return

        language = self._detect_language()
        func_name = self.symbol_info.get("name", "unknown")
        # Strip class scope prefix (e.g. "ClassName.methodName" → "methodName")
        # Red Dragon IR labels use bare method names
        if "." in func_name:
            func_name = func_name.rsplit(".", 1)[-1]

        self.analysis = self.facade.analyze_function(
            source=source,
            language=language,
            function_name=func_name,
        )
        self.app.call_from_thread(self._populate_tabs)

    def _extract_function_source(self) -> str:
        """Read function source from file using symbol line info."""
        repo_root = Path(self.repo.path).expanduser().resolve()
        full_path = repo_root / self.file_path

        if not full_path.exists():
            return ""

        try:
            lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            self.app.call_from_thread(self._show_error, f"Could not read {full_path}: {e}")
            return ""

        start_line = int(self.symbol_info.get("line", "1")) - 1

        # Try to find the end of the function (use end if available, else heuristic)
        # For now, take a reasonable chunk (up to next function or 200 lines)
        end_line = min(start_line + 200, len(lines))

        # Simple heuristic: look for next function/class definition at same or lower indent
        if start_line < len(lines):
            base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            for i in range(start_line + 1, min(start_line + 500, len(lines))):
                line = lines[i]
                if line.strip() == "":
                    continue
                current_indent = len(line) - len(line.lstrip())
                # Check for def/function/class at same or lower indent
                stripped = line.lstrip()
                if current_indent <= base_indent and any(
                    stripped.startswith(kw) for kw in ["def ", "class ", "function ", "public ", "private ", "protected ", "static ", "fn "]
                ):
                    end_line = i
                    break

        return "\n".join(lines[start_line:end_line])

    def _detect_language(self) -> str:
        """Detect language from symbol info or file extension."""
        lang = self.symbol_info.get("language", "").lower()
        if lang:
            lang_map = {
                "java": "java", "python": "python", "javascript": "javascript",
                "typescript": "typescript", "go": "go", "rust": "rust",
                "ruby": "ruby", "php": "php", "c": "c", "c++": "cpp",
                "c#": "csharp", "kotlin": "kotlin", "scala": "scala",
            }
            return lang_map.get(lang, lang)

        ext = self.file_path.rsplit(".", 1)[-1] if "." in self.file_path else ""
        ext_map = {
            "py": "python", "java": "java", "js": "javascript",
            "ts": "typescript", "go": "go", "rs": "rust",
            "rb": "ruby", "php": "php", "c": "c", "cpp": "cpp",
            "cs": "csharp", "kt": "kotlin", "scala": "scala",
        }
        return ext_map.get(ext, "python")

    def _populate_tabs(self) -> None:
        if not self.analysis:
            return

        if self.analysis.error:
            self._show_error(self.analysis.error)
            return

        # IR tab
        if self.analysis.ir_instructions:
            ir_viewer = self.query_one("#ir-viewer", IRViewer)
            ir_viewer.populate(self.analysis.ir_instructions)

        # CFG tab
        if self.analysis.cfg:
            cfg_viewer = self.query_one("#cfg-viewer", CFGViewer)
            cfg_viewer.display_cfg(
                self.analysis.cfg,
                self.analysis.cfg_mermaid,
            )

        # VM State tab
        if self.analysis.vm_state:
            vm_viewer = self.query_one("#vm-state-viewer", VMStateViewer)
            vm_viewer.display_state(self.analysis.vm_state)

        # Dataflow tab
        if self.analysis.dataflow:
            df_viewer = self.query_one("#dataflow-viewer", DataflowViewer)
            df_viewer.populate(self.analysis.dataflow)

        # Update chat context
        chat = self.query_one("#chat-pane", ChatPane)
        chat.set_analysis_context(self.analysis, self.bundle, self.file_path)

    def _show_error(self, message: str) -> None:
        ir_viewer = self.query_one("#ir-viewer", IRViewer)
        ir_viewer.clear()
        ir_viewer.write(f"[#f7768e]Error: {message}[/]")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_open_cfg_external(self) -> None:
        try:
            cfg_viewer = self.query_one("#cfg-viewer", CFGViewer)
            cfg_viewer.open_external()
        except Exception as e:
            cfg_viewer = self.query_one("#cfg-viewer", CFGViewer)
            display = cfg_viewer.query_one("#cfg-display")
            display.write(f"\n[#f7768e]Error opening CFG: {e}[/]")

    def action_toggle_dataflow(self) -> None:
        try:
            df_viewer = self.query_one("#dataflow-viewer", DataflowViewer)
            df_viewer.toggle_view()
        except Exception as e:
            self._show_error(f"Could not toggle dataflow view: {e}")
