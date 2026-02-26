"""Builds system prompt from current view state for LLM context."""

from __future__ import annotations

from typing import Any

from retui.facade.types import FunctionAnalysis, SurveyBundle


def build_system_prompt(
    repo_name: str,
    file_path: str = "",
    analysis: FunctionAnalysis | None = None,
    bundle: SurveyBundle | None = None,
) -> str:
    """Build a context-rich system prompt so the LLM knows what the user is viewing."""
    parts = [
        "You are an expert reverse engineering assistant integrated into a code analysis TUI.",
        "You help engineers understand unfamiliar codebases by answering questions about the code they are currently viewing.",
        f"\nThe user is exploring repository: {repo_name}",
    ]

    if file_path:
        parts.append(f"Currently viewing file: {file_path}")

    if bundle:
        if bundle.languages:
            parts.append(f"Languages detected: {', '.join(bundle.languages)}")
        if bundle.frameworks:
            parts.append(f"Frameworks detected: {', '.join(bundle.frameworks)}")

        # Add integration context for the current file
        if file_path:
            signals = bundle.signals_for_file(file_path)
            if signals:
                parts.append(f"\nIntegration signals in this file ({len(signals)} found):")
                for sig in signals[:10]:
                    itype = sig.integration_type.value if hasattr(sig.integration_type, "value") else str(sig.integration_type)
                    direction = sig.direction.value if hasattr(sig.direction, "value") else str(sig.direction)
                    parts.append(f"  - Line {sig.match.line_number}: {itype} ({direction})")

    if analysis:
        parts.append(f"\nCurrently analyzing function: {analysis.function_name}")
        parts.append(f"Language: {analysis.language}")

        if analysis.ir_instructions:
            parts.append(f"\nIR Instructions ({len(analysis.ir_instructions)} total):")
            for inst in analysis.ir_instructions[:30]:
                parts.append(f"  {inst}")

        if analysis.vm_state:
            state_dict = analysis.vm_state.to_dict()
            parts.append(f"\nVM State summary:")
            if analysis.vm_state.heap:
                parts.append(f"  Heap objects: {len(analysis.vm_state.heap)}")
            if analysis.vm_state.call_stack:
                parts.append(f"  Call stack depth: {len(analysis.vm_state.call_stack)}")
            if analysis.vm_state.path_conditions:
                parts.append(f"  Path conditions: {analysis.vm_state.path_conditions}")

        if analysis.dataflow and hasattr(analysis.dataflow, "def_use_chains"):
            parts.append(f"\nDataflow chains ({len(analysis.dataflow.def_use_chains)} links):")
            for link in analysis.dataflow.def_use_chains[:15]:
                parts.append(
                    f"  {link.definition.variable}@{link.definition.block_label} -> "
                    f"{link.use.variable}@{link.use.block_label}"
                )

        if analysis.source:
            parts.append(f"\nFunction source code:\n```\n{analysis.source[:3000]}\n```")

    parts.append(
        "\nProvide concise, technical answers. Reference specific lines, variables, and dataflow when relevant."
    )

    return "\n".join(parts)
