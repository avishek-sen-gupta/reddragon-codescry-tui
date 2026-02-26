"""Tests for the analysis facade types."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from retui.facade.types import FunctionAnalysis, SurveyBundle


@dataclass
class MockCTagsEntry:
    name: str
    path: str
    kind: str
    line: int
    end: int | None = None
    scope: str = ""
    scope_kind: str = ""
    signature: str = ""
    language: str = "Python"


@dataclass
class MockFileMatch:
    file_path: str
    line_number: int
    line_content: str = ""
    language: str | None = None


@dataclass
class MockIntegrationType:
    value: str = "http_rest"


@dataclass
class MockConfidence:
    value: str = "high"


@dataclass
class MockDirection:
    value: str = "inward"


@dataclass
class MockSignal:
    match: MockFileMatch
    integration_type: MockIntegrationType
    confidence: MockConfidence
    direction: MockDirection
    matched_pattern: str = ""
    entity_type: str = "file_content"
    source: str = "test"


@dataclass
class MockCTagsResult:
    entries: list[MockCTagsEntry]
    success: bool = True


@dataclass
class MockIntegrationResult:
    integration_points: list[MockSignal]
    files_scanned: int = 1


@dataclass
class MockReport:
    languages: list[str]
    frameworks: list[str]


class TestSurveyBundle:
    def test_languages_and_frameworks(self) -> None:
        bundle = SurveyBundle(
            repo_path="/test",
            report=MockReport(languages=["Python", "Java"], frameworks=["Flask"]),
            ctags=MockCTagsResult(entries=[]),
            integrations=MockIntegrationResult(integration_points=[]),
            resolution=None,
            concretisation=None,
        )
        assert bundle.languages == ["Python", "Java"]
        assert bundle.frameworks == ["Flask"]

    def test_symbols_for_file(self) -> None:
        entries = [
            MockCTagsEntry(name="foo", path="src/main.py", kind="function", line=10),
            MockCTagsEntry(name="bar", path="src/main.py", kind="function", line=20),
            MockCTagsEntry(name="baz", path="src/other.py", kind="function", line=5),
        ]
        bundle = SurveyBundle(
            repo_path="/test",
            report=MockReport(languages=[], frameworks=[]),
            ctags=MockCTagsResult(entries=entries),
            integrations=MockIntegrationResult(integration_points=[]),
            resolution=None,
            concretisation=None,
        )
        syms = bundle.symbols_for_file("src/main.py")
        assert len(syms) == 2
        assert all(s.path == "src/main.py" for s in syms)

    def test_signals_for_file(self) -> None:
        signals = [
            MockSignal(
                match=MockFileMatch(file_path="src/api.py", line_number=14),
                integration_type=MockIntegrationType("http_rest"),
                confidence=MockConfidence("high"),
                direction=MockDirection("inward"),
            ),
            MockSignal(
                match=MockFileMatch(file_path="src/db.py", line_number=48),
                integration_type=MockIntegrationType("database"),
                confidence=MockConfidence("high"),
                direction=MockDirection("outward"),
            ),
        ]
        bundle = SurveyBundle(
            repo_path="/test",
            report=MockReport(languages=[], frameworks=[]),
            ctags=MockCTagsResult(entries=[]),
            integrations=MockIntegrationResult(integration_points=signals),
            resolution=None,
            concretisation=None,
        )
        api_signals = bundle.signals_for_file("src/api.py")
        assert len(api_signals) == 1
        assert api_signals[0].match.line_number == 14


class TestFunctionAnalysis:
    def test_error_state(self) -> None:
        fa = FunctionAnalysis(
            function_name="test_fn",
            source="def test(): pass",
            language="python",
            error="Parse error",
        )
        assert fa.error == "Parse error"
        assert fa.ir_instructions == []
        assert fa.cfg is None

    def test_successful_state(self) -> None:
        fa = FunctionAnalysis(
            function_name="test_fn",
            source="def test(): return 42",
            language="python",
            ir_instructions=["mock_ir"],
            cfg_mermaid="flowchart TD",
        )
        assert fa.error is None
        assert len(fa.ir_instructions) == 1
        assert fa.cfg_mermaid == "flowchart TD"
