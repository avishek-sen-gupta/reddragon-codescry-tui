"""Tests for ChatScreen construction and configuration."""

from __future__ import annotations

from types import SimpleNamespace

from retui.screens.chat_screen import ChatScreen


def _make_config():
    return SimpleNamespace(
        llm=SimpleNamespace(model="test/model", api_key_env="TEST_KEY"),
    )


def _make_analysis():
    return SimpleNamespace(
        ir_instructions=[],
        cfg=None,
        cfg_mermaid="",
        vm_state=None,
        dataflow=None,
        execution_trace=None,
        error=None,
    )


class TestChatScreenInit:
    def test_stores_config(self):
        config = _make_config()
        screen = ChatScreen(
            config=config,
            repo_name="my-repo",
            analysis=None,
            bundle=None,
            file_path="src/main.py",
        )
        assert screen.config is config
        assert screen.repo_name == "my-repo"
        assert screen._file_path == "src/main.py"

    def test_stores_analysis_context(self):
        analysis = _make_analysis()
        bundle = SimpleNamespace(survey=None)
        screen = ChatScreen(
            config=_make_config(),
            repo_name="repo",
            analysis=analysis,
            bundle=bundle,
            file_path="foo.py",
        )
        assert screen._analysis is analysis
        assert screen._bundle is bundle

    def test_none_analysis_is_accepted(self):
        screen = ChatScreen(
            config=_make_config(),
            repo_name="repo",
            analysis=None,
            bundle=None,
            file_path="",
        )
        assert screen._analysis is None
