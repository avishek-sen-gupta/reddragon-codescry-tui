"""Data transfer objects wrapping codescry + red-dragon results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SurveyBundle:
    """Groups all codescry survey results for a repo."""

    repo_path: str
    report: Any  # SurveyReport
    ctags: Any  # CTagsResult
    integrations: Any  # IntegrationDetectorResult
    resolution: Any  # ResolutionResult
    concretisation: Any  # ConcretisationResult
    embedding_metadata: dict = field(default_factory=dict)  # Per-signal BGE scores

    @property
    def languages(self) -> list[str]:
        return self.report.languages if self.report else []

    @property
    def frameworks(self) -> list[str]:
        return self.report.frameworks if self.report else []

    @property
    def all_symbols(self) -> list[Any]:
        return self.ctags.entries if self.ctags and self.ctags.success else []

    @property
    def all_signals(self) -> list[Any]:
        return self.integrations.integration_points if self.integrations else []

    @property
    def concretised_signals(self) -> list[Any]:
        """Return concretised signals (SIGNAL only, not NOISE) if available."""
        if not self.concretisation or not hasattr(self.concretisation, "concretised"):
            return []
        return [s for s in self.concretisation.concretised if s.is_integration]

    @property
    def has_embedding_concretisation(self) -> bool:
        return bool(self.embedding_metadata)

    def symbols_for_file(self, file_path: str) -> list[Any]:
        """Filter CTags entries to a specific file (relative path match)."""
        return [e for e in self.all_symbols if e.path.endswith(file_path) or file_path.endswith(e.path)]

    def signals_for_file(self, file_path: str) -> list[Any]:
        """Filter integration signals to a specific file."""
        return [
            s for s in self.all_signals
            if s.match.file_path.endswith(file_path) or file_path.endswith(s.match.file_path)
        ]

    def concretised_signals_for_file(self, file_path: str) -> list[Any]:
        """Filter concretised signals to a specific file."""
        return [
            s for s in self.concretised_signals
            if s.original_signal.match.file_path.endswith(file_path)
            or file_path.endswith(s.original_signal.match.file_path)
        ]

    def embedding_score_for_signal(self, file_path: str, line_number: int) -> dict | None:
        """Get BGE embedding metadata for a specific signal."""
        return self.embedding_metadata.get((file_path, line_number))


@dataclass
class FunctionAnalysis:
    """Groups all red-dragon analysis results for a function."""

    function_name: str
    source: str
    language: str
    ir_instructions: list[Any] = field(default_factory=list)
    cfg: Any = None  # CFG
    vm_state: Any = None  # VMState
    dataflow: Any = None  # DataflowResult
    registry: Any = None  # FunctionRegistry
    cfg_mermaid: str = ""
    error: str | None = None
