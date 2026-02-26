"""Tests for session config and persistence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from retui.session.config import AppConfig, RepoConfig, LLMConfig
from retui.session.models import ChatMessage, SessionMeta
from retui.session.persistence import SessionManager


@pytest.fixture
def sample_config_path(tmp_path: Path) -> Path:
    config = {
        "version": 1,
        "repos": [
            {"name": "test-repo", "path": "/tmp/test-repo", "languages": ["Python"], "auto_survey": True},
            {"name": "other-repo", "path": "/tmp/other", "languages": ["Java"]},
        ],
        "session_dir": str(tmp_path / "sessions"),
        "llm": {"provider": "claude", "model": "claude-sonnet-4-20250514", "api_key_env": "ANTHROPIC_API_KEY"},
    }
    p = tmp_path / "repos.json"
    p.write_text(json.dumps(config))
    return p


class TestAppConfig:
    def test_load_config(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        assert config.version == 1
        assert len(config.repos) == 2
        assert config.repos[0].name == "test-repo"
        assert config.repos[0].languages == ["Python"]
        assert config.repos[0].auto_survey is True
        assert config.repos[1].auto_survey is False

    def test_llm_config(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        assert config.llm.provider == "claude"
        assert config.llm.model == "claude-sonnet-4-20250514"

    def test_session_path(self, sample_config_path: Path, tmp_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        assert "sessions" in str(config.session_path)

    def test_default_config(self) -> None:
        config = AppConfig()
        assert config.version == 1
        assert config.repos == []
        assert config.llm.provider == "claude"
        assert config.neo4j.enabled is False


class TestSessionPersistence:
    def test_save_and_load_meta(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        manager = SessionManager(config)

        meta = SessionMeta(last_screen="RepoScreen", last_repo="test-repo")
        manager.save_meta(meta)

        loaded = manager.load_meta()
        assert loaded.last_screen == "RepoScreen"
        assert loaded.last_repo == "test-repo"

    def test_load_meta_default(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        manager = SessionManager(config)
        manager.ensure_dirs()

        loaded = manager.load_meta()
        assert loaded.last_screen == "dashboard"

    def test_chat_history(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        manager = SessionManager(config)

        manager.append_chat_message("test-repo", ChatMessage(role="user", content="Hello"))
        manager.append_chat_message("test-repo", ChatMessage(role="assistant", content="Hi there"))

        history = manager.load_chat_history("test-repo")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"

    def test_clear_chat_history(self, sample_config_path: Path) -> None:
        config = AppConfig.load(sample_config_path)
        manager = SessionManager(config)

        manager.append_chat_message("test-repo", ChatMessage(role="user", content="Hello"))
        manager.clear_chat_history("test-repo")

        history = manager.load_chat_history("test-repo")
        assert len(history) == 0
