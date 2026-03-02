"""FunctionScreen — deep-dive with IR, CFG, Dataflow, Execute tabs + Chat."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static, TabbedContent, TabPane

from retui.facade.types import FunctionAnalysis, SurveyBundle
from retui.session.config import AppConfig, RepoConfig
from retui.widgets.cfg_viewer import CFGViewer
from retui.widgets.dataflow_viewer import DataflowViewer
from retui.widgets.execution_replay_viewer import ExecutionReplayViewer
from retui.widgets.ir_viewer import IRViewer
from retui.widgets.status_bar import StatusBar


class FunctionScreen(Screen):
    """Displays IR, CFG, dataflow, and execution replay tabs with LLM chat."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("o", "open_cfg_external", "Open CFG"),
        ("d", "toggle_dataflow", "Toggle Dataflow View"),
        ("n", "step_forward", "Step Forward"),
        ("p", "step_backward", "Step Backward"),
        ("c", "open_chat", "Chat"),
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
        with Vertical(id="analysis-panel", classes="panel"):
            with TabbedContent(id="analysis-tabs"):
                with TabPane("IR", id="ir-tab"):
                    yield IRViewer(id="ir-viewer")
                with TabPane("CFG", id="cfg-tab"):
                    yield CFGViewer(id="cfg-viewer")
                with TabPane("Dataflow", id="dataflow-tab"):
                    yield DataflowViewer(id="dataflow-viewer")
                with TabPane("Execute", id="execute-tab"):
                    yield ExecutionReplayViewer(id="execution-replay")
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
        short_file = (
            self.file_path.rsplit("/", 1)[-1]
            if "/" in self.file_path
            else self.file_path
        )
        func_name = self.symbol_info.get("name", "?")
        bar.breadcrumb = ["Dashboard", self.repo.name, short_file, f"{func_name}()"]
        bar.hints = [
            ("Esc", "Back"),
            ("o", "Open CFG"),
            ("d", "Toggle Dataflow"),
            ("n/p", "Step Fwd/Back"),
            ("c", "Chat"),
            ("q", "Quit"),
        ]

    @work(thread=True, description="Analyzing function...")
    def _run_analysis(self) -> None:
        """Extract function source via tree-sitter and run red-dragon analysis."""
        language = self._detect_language()
        func_name = self.symbol_info.get("name", "unknown")
        # Strip class scope prefix (e.g. "ClassName.methodName" → "methodName")
        # Red Dragon IR labels use bare method names
        if "." in func_name:
            func_name = func_name.rsplit(".", 1)[-1]

        if language == "cobol":
            source = self._read_entire_file()
            frontend_type = "cobol"
        else:
            source = self._extract_function_source(func_name, language)
            frontend_type = "deterministic"

        if not source:
            self.app.call_from_thread(
                self._show_error, "Could not extract function source."
            )
            return

        self.analysis = self.facade.analyze_function(
            source=source,
            language=language,
            function_name=func_name,
            frontend_type=frontend_type,
        )
        self.app.call_from_thread(self._populate_tabs)

    def _read_entire_file(self) -> str:
        """Read the entire source file for whole-program analysis (e.g. COBOL)."""
        repo_root = Path(self.repo.path).expanduser().resolve()
        full_path = repo_root / self.file_path

        if not full_path.exists():
            return ""

        try:
            return full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.app.call_from_thread(
                self._show_error, f"Could not read {full_path}: {e}"
            )
            return ""

    def _extract_function_source(self, func_name: str, language: str) -> str:
        """Extract function source using Red Dragon's tree-sitter AST extraction."""
        repo_root = Path(self.repo.path).expanduser().resolve()
        full_path = repo_root / self.file_path

        if not full_path.exists():
            return ""

        try:
            file_source = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.app.call_from_thread(
                self._show_error, f"Could not read {full_path}: {e}"
            )
            return ""

        try:
            from interpreter.api import extract_function_source

            return extract_function_source(file_source, func_name, language)
        except ValueError as e:
            self.app.call_from_thread(self._show_error, str(e))
            return ""
        except Exception as e:
            self.app.call_from_thread(
                self._show_error, f"Source extraction failed: {e}"
            )
            return ""

    def _detect_language(self) -> str:
        """Detect language from symbol info or file extension."""
        lang = self.symbol_info.get("language", "").lower()
        if lang:
            lang_map = {
                "java": "java",
                "python": "python",
                "javascript": "javascript",
                "typescript": "typescript",
                "go": "go",
                "rust": "rust",
                "ruby": "ruby",
                "php": "php",
                "c": "c",
                "c++": "cpp",
                "c#": "csharp",
                "kotlin": "kotlin",
                "scala": "scala",
                "cobol": "cobol",
            }
            return lang_map.get(lang, lang)

        ext = self.file_path.rsplit(".", 1)[-1] if "." in self.file_path else ""
        ext_map = {
            "py": "python",
            "java": "java",
            "js": "javascript",
            "ts": "typescript",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "php": "php",
            "c": "c",
            "cpp": "cpp",
            "cs": "csharp",
            "kt": "kotlin",
            "scala": "scala",
            "cbl": "cobol",
            "cob": "cobol",
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

        # Dataflow tab
        if self.analysis.dataflow:
            df_viewer = self.query_one("#dataflow-viewer", DataflowViewer)
            df_viewer.populate(self.analysis.dataflow)

        # Execute tab
        if self.analysis.execution_trace:
            replay = self.query_one("#execution-replay", ExecutionReplayViewer)
            replay.set_trace(
                self.analysis.execution_trace, self.analysis.ir_instructions
            )

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

    def action_step_forward(self) -> None:
        replay = self.query_one("#execution-replay", ExecutionReplayViewer)
        replay.step_forward()

    def action_step_backward(self) -> None:
        replay = self.query_one("#execution-replay", ExecutionReplayViewer)
        replay.step_backward()

    def action_open_chat(self) -> None:
        from retui.screens.chat_screen import ChatScreen

        self.app.push_screen(
            ChatScreen(
                config=self.config,
                repo_name=self.repo.name,
                analysis=self.analysis,
                bundle=self.bundle,
                file_path=self.file_path,
            )
        )
