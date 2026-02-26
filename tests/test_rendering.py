"""Tests for CFG rendering utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from retui.rendering.dot_utils import cfg_to_dot


@dataclass
class MockIRInstruction:
    opcode: str = "CONST"
    result_reg: str = "%0"
    operands: list = field(default_factory=lambda: [42])
    label: str | None = None
    source_location: str | None = None

    def __str__(self) -> str:
        parts = []
        if self.result_reg:
            parts.append(f"{self.result_reg} =")
        parts.append(self.opcode)
        parts.extend(str(o) for o in self.operands)
        return " ".join(parts)


@dataclass
class MockBasicBlock:
    label: str
    instructions: list[MockIRInstruction] = field(default_factory=list)
    successors: list[str] = field(default_factory=list)
    predecessors: list[str] = field(default_factory=list)


@dataclass
class MockCFG:
    blocks: dict[str, MockBasicBlock] = field(default_factory=dict)
    entry: str = "entry"


class TestCfgToDot:
    def test_empty_cfg(self) -> None:
        cfg = MockCFG()
        dot = cfg_to_dot(cfg)
        assert "digraph CFG" in dot
        assert dot.endswith("}")

    def test_single_block(self) -> None:
        block = MockBasicBlock(
            label="entry",
            instructions=[MockIRInstruction()],
            successors=[],
        )
        cfg = MockCFG(blocks={"entry": block}, entry="entry")
        dot = cfg_to_dot(cfg)
        assert '"entry"' in dot
        assert "CONST" in dot

    def test_edges(self) -> None:
        entry = MockBasicBlock(label="entry", successors=["then", "else"])
        then_block = MockBasicBlock(label="then", predecessors=["entry"])
        else_block = MockBasicBlock(label="else", predecessors=["entry"])
        cfg = MockCFG(
            blocks={"entry": entry, "then": then_block, "else": else_block},
            entry="entry",
        )
        dot = cfg_to_dot(cfg)
        assert '"entry" -> "then"' in dot
        assert '"entry" -> "else"' in dot

    def test_entry_block_colored(self) -> None:
        block = MockBasicBlock(label="entry")
        cfg = MockCFG(blocks={"entry": block}, entry="entry")
        dot = cfg_to_dot(cfg)
        # Entry block should have special color
        assert "#414868" in dot
