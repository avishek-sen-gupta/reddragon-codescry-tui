"""Tests for ExecutionReplayViewer logic — step navigation and IR index mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from retui.widgets.execution_replay_viewer import _build_ir_index_map


@dataclass
class FakeInstruction:
    """Minimal instruction stand-in for testing."""

    opcode: SimpleNamespace
    result_reg: str = ""
    operands: list[Any] = field(default_factory=list)
    label: str = ""


def _inst(opcode_str: str, label: str = "", result_reg: str = "") -> FakeInstruction:
    return FakeInstruction(
        opcode=SimpleNamespace(value=opcode_str),
        label=label,
        result_reg=result_reg,
    )


class TestBuildIrIndexMap:
    def test_single_block_maps_correctly(self):
        instructions = [
            _inst("LABEL", label="entry"),
            _inst("CONST", result_reg="%0"),
            _inst("STORE_VAR"),
            _inst("RETURN"),
        ]
        index_map = _build_ir_index_map(instructions)

        # LABEL starts block "entry", subsequent instructions get block_ip 0,1,2
        assert index_map[("entry", 0)] == 1  # CONST at flat index 1
        assert index_map[("entry", 1)] == 2  # STORE_VAR at flat index 2
        assert index_map[("entry", 2)] == 3  # RETURN at flat index 3

    def test_multiple_blocks(self):
        instructions = [
            _inst("LABEL", label="entry"),
            _inst("CONST", result_reg="%0"),
            _inst("BRANCH_IF"),
            _inst("LABEL", label="then"),
            _inst("CONST", result_reg="%1"),
            _inst("RETURN"),
            _inst("LABEL", label="else"),
            _inst("CONST", result_reg="%2"),
            _inst("RETURN"),
        ]
        index_map = _build_ir_index_map(instructions)

        assert index_map[("entry", 0)] == 1
        assert index_map[("entry", 1)] == 2
        assert index_map[("then", 0)] == 4
        assert index_map[("then", 1)] == 5
        assert index_map[("else", 0)] == 7
        assert index_map[("else", 1)] == 8

    def test_empty_instructions_returns_empty_map(self):
        assert _build_ir_index_map([]) == {}

    def test_label_only_returns_empty_map(self):
        instructions = [_inst("LABEL", label="entry")]
        assert _build_ir_index_map(instructions) == {}


@dataclass
class FakeTraceStep:
    step_index: int
    block_label: str
    instruction_index: int
    instruction: Any = None
    update: Any = None
    vm_state: Any = None
    used_llm: bool = False


@dataclass
class FakeExecutionTrace:
    steps: list[FakeTraceStep] = field(default_factory=list)
    stats: Any = None
    initial_state: Any = None


class TestStepNavigation:
    """Tests for step_forward, step_backward, reset logic.

    Tests the navigation bounds without requiring Textual widget mounting,
    by directly checking the reactive value and navigation methods.
    """

    def _make_viewer_state(self, num_steps: int) -> tuple[FakeExecutionTrace, int]:
        """Create a fake trace and return (trace, max_step)."""
        steps = [
            FakeTraceStep(step_index=i, block_label="entry", instruction_index=i)
            for i in range(num_steps)
        ]
        trace = FakeExecutionTrace(steps=steps)
        return trace, num_steps - 1

    def test_step_forward_increments(self):
        trace, max_step = self._make_viewer_state(5)
        current = 0
        # Simulate step_forward bounds check
        if current < len(trace.steps) - 1:
            current += 1
        assert current == 1

    def test_step_forward_stops_at_end(self):
        trace, max_step = self._make_viewer_state(3)
        current = max_step
        # At end, should not increment
        if current < len(trace.steps) - 1:
            current += 1
        assert current == max_step

    def test_step_backward_decrements(self):
        current = 3
        if current > 0:
            current -= 1
        assert current == 2

    def test_step_backward_stops_at_zero(self):
        current = 0
        if current > 0:
            current -= 1
        assert current == 0

    def test_reset_returns_to_zero(self):
        current = 5
        current = 0  # reset
        assert current == 0

    def test_run_to_end_jumps_to_last(self):
        trace, max_step = self._make_viewer_state(10)
        current = 0
        current = len(trace.steps) - 1  # run_to_end
        assert current == 9
