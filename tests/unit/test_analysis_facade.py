"""Tests for AnalysisFacade.analyze_function — COBOL frontend routing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from retui.facade.analysis import AnalysisFacade, _FRONTEND_COBOL


class FakeIRInstruction:
    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


class FakeCFG:
    def __init__(self) -> None:
        self.blocks = {"entry": SimpleNamespace(instructions=[])}


class FakeTrace:
    def __init__(self) -> None:
        self.steps = []


@dataclass
class RecordingRedDragonAPI:
    """A stub RedDragonAPI that records all calls for assertion."""

    instructions: list = field(default_factory=lambda: [FakeIRInstruction("CONST 1")])
    cfg: Any = field(default_factory=FakeCFG)
    trace: Any = field(default_factory=FakeTrace)

    lower_source_calls: list = field(default_factory=list)
    build_cfg_calls: list = field(default_factory=list)
    dump_mermaid_calls: list = field(default_factory=list)
    execute_traced_calls: list = field(default_factory=list)

    def lower_source(
        self, source, language, frontend_type="deterministic", backend="claude"
    ):
        self.lower_source_calls.append(
            {
                "source": source,
                "language": language,
                "frontend_type": frontend_type,
                "backend": backend,
            }
        )
        return self.instructions

    def build_cfg_from_source(
        self,
        source,
        language,
        frontend_type="deterministic",
        backend="claude",
        function_name="",
    ):
        self.build_cfg_calls.append(
            {
                "source": source,
                "language": language,
                "frontend_type": frontend_type,
                "function_name": function_name,
            }
        )
        return self.cfg

    def dump_mermaid(
        self,
        source,
        language,
        frontend_type="deterministic",
        backend="claude",
        function_name="",
    ):
        self.dump_mermaid_calls.append(
            {"frontend_type": frontend_type, "function_name": function_name}
        )
        return "flowchart TD\n  entry"

    def execute_traced(
        self,
        source,
        language,
        function_name="",
        entry_point="",
        frontend_type="deterministic",
        backend="claude",
        max_steps=100,
    ):
        self.execute_traced_calls.append(
            {"frontend_type": frontend_type, "function_name": function_name}
        )
        return self.trace

    def dataflow_analyze(self, cfg):
        return {"entry": {}}

    def build_registry(self, instructions, cfg):
        return {}


class TestAnalyzeFunctionCobol:
    def test_cobol_frontend_type_passes_through_to_lower_source(self, monkeypatch):
        api = RecordingRedDragonAPI()
        monkeypatch.setattr(
            "retui.facade.analysis.AnalysisFacade._ensure_proleap_jar",
            lambda self: None,
        )

        facade = AnalysisFacade(red_dragon_api=api)
        facade.analyze_function(
            source="IDENTIFICATION DIVISION.\n",
            language="cobol",
            function_name="MAIN-PARA",
            frontend_type=_FRONTEND_COBOL,
        )

        assert len(api.lower_source_calls) == 1
        assert api.lower_source_calls[0]["frontend_type"] == "cobol"

    def test_cobol_skips_function_scoping(self, monkeypatch):
        api = RecordingRedDragonAPI()
        monkeypatch.setattr(
            "retui.facade.analysis.AnalysisFacade._ensure_proleap_jar",
            lambda self: None,
        )

        facade = AnalysisFacade(red_dragon_api=api)
        facade.analyze_function(
            source="IDENTIFICATION DIVISION.\n",
            language="cobol",
            function_name="MAIN-PARA",
            frontend_type=_FRONTEND_COBOL,
        )

        # All scoped calls should use function_name="" for COBOL
        assert api.build_cfg_calls[0]["function_name"] == ""
        assert api.execute_traced_calls[0]["function_name"] == ""
        assert api.dump_mermaid_calls[0]["function_name"] == ""

    def test_deterministic_preserves_function_scoping(self):
        api = RecordingRedDragonAPI()
        facade = AnalysisFacade(red_dragon_api=api)

        facade.analyze_function(
            source="def foo(): pass\n",
            language="python",
            function_name="foo",
            frontend_type="deterministic",
        )

        assert api.build_cfg_calls[0]["function_name"] == "foo"
        assert api.execute_traced_calls[0]["function_name"] == "foo"
        assert api.dump_mermaid_calls[0]["function_name"] == "foo"

    def test_cobol_triggers_ensure_proleap_jar(self):
        api = RecordingRedDragonAPI()
        jar_checked = []

        class TestFacade(AnalysisFacade):
            def _ensure_proleap_jar(self):
                jar_checked.append(True)

        facade = TestFacade(red_dragon_api=api)
        facade.analyze_function(
            source="IDENTIFICATION DIVISION.\n",
            language="cobol",
            function_name="MAIN-PARA",
            frontend_type=_FRONTEND_COBOL,
        )

        assert jar_checked == [True]

    def test_deterministic_does_not_trigger_ensure_proleap_jar(self):
        api = RecordingRedDragonAPI()
        jar_checked = []

        class TestFacade(AnalysisFacade):
            def _ensure_proleap_jar(self):
                jar_checked.append(True)

        facade = TestFacade(red_dragon_api=api)
        facade.analyze_function(
            source="def foo(): pass\n",
            language="python",
            function_name="foo",
            frontend_type="deterministic",
        )

        assert jar_checked == []


class TestEnsureProleapJar:
    def test_does_not_overwrite_existing_env_var(self, monkeypatch):
        monkeypatch.setenv("PROLEAP_BRIDGE_JAR", "/custom/path.jar")
        facade = AnalysisFacade()
        facade._ensure_proleap_jar()
        assert os.environ["PROLEAP_BRIDGE_JAR"] == "/custom/path.jar"

    def test_sets_jar_path_when_jar_exists(self, monkeypatch, tmp_path):
        monkeypatch.delenv("PROLEAP_BRIDGE_JAR", raising=False)

        # Create a fake interpreter package with __file__
        fake_interpreter_dir = tmp_path / "interpreter"
        fake_interpreter_dir.mkdir()
        init_file = fake_interpreter_dir / "__init__.py"
        init_file.write_text("")

        # Create the expected JAR path
        jar_dir = tmp_path / "proleap-bridge" / "target"
        jar_dir.mkdir(parents=True)
        jar_file = jar_dir / "proleap-bridge-0.1.0-shaded.jar"
        jar_file.write_text("fake jar")

        # Patch interpreter module's __file__
        import sys
        import types

        fake_module = types.ModuleType("interpreter")
        fake_module.__file__ = str(init_file)
        monkeypatch.setitem(sys.modules, "interpreter", fake_module)

        facade = AnalysisFacade()
        facade._ensure_proleap_jar()

        assert os.environ.get("PROLEAP_BRIDGE_JAR") == str(jar_file)
