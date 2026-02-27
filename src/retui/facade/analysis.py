"""AnalysisFacade — unified API over codescry and red-dragon."""

from __future__ import annotations

from typing import Any

from retui.facade.types import FunctionAnalysis, SurveyBundle
from retui.session.config import EmbeddingConfig


class AnalysisFacade:
    """Unified analysis API caching results in-memory."""

    def __init__(self, embedding_config: EmbeddingConfig | None = None) -> None:
        self._survey_cache: dict[str, SurveyBundle] = {}
        self._function_cache: dict[tuple[str, str], FunctionAnalysis] = {}
        self._embedding_config = embedding_config or EmbeddingConfig()
        self._bge_client = None

    def _get_bge_client(self):
        """Lazily initialise the BGE embedding client."""
        if self._bge_client is None:
            from repo_surveyor.integration_concretiser.embedding_concretiser import (
                BGEEmbeddingClient,
            )

            self._bge_client = BGEEmbeddingClient(
                model_name=self._embedding_config.model,
                device=self._embedding_config.device,
            )
        return self._bge_client

    def survey_repo(
        self, repo_path: str, languages: list[str] | None = None
    ) -> SurveyBundle:
        """Run a full codescry survey + BGE embedding concretisation."""
        if repo_path in self._survey_cache:
            return self._survey_cache[repo_path]

        from repo_surveyor import survey, Language

        lang_objs: list[Language] = []
        if languages:
            for lang_name in languages:
                lang = Language.from_name(lang_name)
                if lang:
                    lang_objs.append(lang)

        report, ctags, integrations, resolution, concretisation = survey(
            repo_path=repo_path,
            languages=lang_objs,
        )

        # Run BGE embedding concretisation if enabled
        embedding_metadata: dict = {}
        if self._embedding_config.enabled and integrations.integration_points:
            try:
                from pathlib import Path
                from repo_surveyor.integration_concretiser.pattern_embedding_concretiser import (
                    PatternEmbeddingConcretiser,
                )

                client = self._get_bge_client()
                cache_path = (
                    Path(self._embedding_config.cache_path)
                    if self._embedding_config.cache_path
                    else Path(".")
                )
                concretiser = PatternEmbeddingConcretiser(
                    client,
                    threshold=self._embedding_config.threshold,
                    cache_path=cache_path,
                )
                concretisation, embedding_metadata = concretiser.concretise(
                    integrations
                )
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning("BGE concretisation failed: %s", e)

        bundle = SurveyBundle(
            repo_path=repo_path,
            report=report,
            ctags=ctags,
            integrations=integrations,
            resolution=resolution,
            concretisation=concretisation,
            embedding_metadata=embedding_metadata,
        )
        self._survey_cache[repo_path] = bundle
        return bundle

    def get_symbols_for_file(self, repo_path: str, file_path: str) -> list[Any]:
        """Get CTags entries for a specific file."""
        bundle = self._survey_cache.get(repo_path)
        if not bundle:
            return []
        return bundle.symbols_for_file(file_path)

    def get_integrations_for_file(self, repo_path: str, file_path: str) -> list[Any]:
        """Get integration signals for a specific file."""
        bundle = self._survey_cache.get(repo_path)
        if not bundle:
            return []
        return bundle.signals_for_file(file_path)

    def analyze_function(
        self,
        source: str,
        language: str,
        function_name: str,
        entry_point: str = "",
        max_steps: int = 100,
    ) -> FunctionAnalysis:
        """Run red-dragon analysis on a function."""
        cache_key = (function_name, source[:200])
        if cache_key in self._function_cache:
            return self._function_cache[cache_key]

        try:
            from interpreter.api import (
                lower_source,
                build_cfg_from_source,
                dump_mermaid,
                execute_traced,
            )
            from interpreter.dataflow import analyze as dataflow_analyze
            from interpreter.registry import build_registry

            # Lower source to IR
            instructions = lower_source(source, language)

            # Build function-scoped CFG via Red Dragon's API
            cfg = build_cfg_from_source(
                source,
                language,
                function_name=function_name,
            )

            # Build registry
            registry = build_registry(instructions, cfg)

            # Dataflow analysis on the function-scoped CFG
            dataflow = dataflow_analyze(cfg)

            # Traced symbolic execution (produces both trace and final state)
            trace = execute_traced(
                source=source,
                language=language,
                function_name=function_name,
                entry_point=entry_point,
                max_steps=max_steps,
            )
            vm_state = trace.steps[-1].vm_state if trace.steps else None

            # Generate Mermaid via Red Dragon's API
            cfg_mermaid = dump_mermaid(
                source,
                language,
                function_name=function_name,
            )

            result = FunctionAnalysis(
                function_name=function_name,
                source=source,
                language=language,
                ir_instructions=instructions,
                cfg=cfg,
                vm_state=vm_state,
                dataflow=dataflow,
                registry=registry,
                execution_trace=trace,
                cfg_mermaid=cfg_mermaid,
            )
        except Exception as e:
            result = FunctionAnalysis(
                function_name=function_name,
                source=source,
                language=language,
                error=str(e),
            )

        self._function_cache[cache_key] = result
        return result

    def clear_cache(self) -> None:
        self._survey_cache.clear()
        self._function_cache.clear()
