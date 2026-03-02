"""Protocol and default implementation for the Red Dragon analysis API."""

from __future__ import annotations

from typing import Any, Protocol


class RedDragonAPI(Protocol):
    """Port for Red Dragon analysis operations."""

    def lower_source(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
    ) -> list[Any]: ...

    def build_cfg_from_source(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
        function_name: str = "",
    ) -> Any: ...

    def dump_mermaid(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
        function_name: str = "",
    ) -> str: ...

    def execute_traced(
        self,
        source: str,
        language: str,
        function_name: str = "",
        entry_point: str = "",
        frontend_type: str = "deterministic",
        backend: str = "claude",
        max_steps: int = 100,
    ) -> Any: ...

    def dataflow_analyze(self, cfg: Any) -> Any: ...

    def build_registry(self, instructions: list[Any], cfg: Any) -> Any: ...


class DefaultRedDragonAPI:
    """Default implementation that delegates to the interpreter package."""

    def lower_source(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
    ) -> list[Any]:
        from interpreter.api import lower_source

        return lower_source(
            source, language, frontend_type=frontend_type, backend=backend
        )

    def build_cfg_from_source(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
        function_name: str = "",
    ) -> Any:
        from interpreter.api import build_cfg_from_source

        return build_cfg_from_source(
            source,
            language,
            frontend_type=frontend_type,
            backend=backend,
            function_name=function_name,
        )

    def dump_mermaid(
        self,
        source: str,
        language: str,
        frontend_type: str = "deterministic",
        backend: str = "claude",
        function_name: str = "",
    ) -> str:
        from interpreter.api import dump_mermaid

        return dump_mermaid(
            source,
            language,
            frontend_type=frontend_type,
            backend=backend,
            function_name=function_name,
        )

    def execute_traced(
        self,
        source: str,
        language: str,
        function_name: str = "",
        entry_point: str = "",
        frontend_type: str = "deterministic",
        backend: str = "claude",
        max_steps: int = 100,
    ) -> Any:
        from interpreter.api import execute_traced

        return execute_traced(
            source=source,
            language=language,
            function_name=function_name,
            entry_point=entry_point,
            frontend_type=frontend_type,
            backend=backend,
            max_steps=max_steps,
        )

    def dataflow_analyze(self, cfg: Any) -> Any:
        from interpreter.dataflow import analyze

        return analyze(cfg)

    def build_registry(self, instructions: list[Any], cfg: Any) -> Any:
        from interpreter.registry import build_registry

        return build_registry(instructions, cfg)
