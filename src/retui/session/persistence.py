"""Save/load session state and caches to JSON."""

from __future__ import annotations

import json
from pathlib import Path

from retui.session.config import AppConfig
from retui.session.models import ChatMessage, SessionMeta


class SessionManager:
    """Manages session persistence to disk."""

    def __init__(self, config: AppConfig) -> None:
        self.base_dir = config.session_path
        self.meta_path = self.base_dir / "session_meta.json"
        self.survey_cache_dir = self.base_dir / "survey_cache"
        self.analysis_cache_dir = self.base_dir / "analysis_cache"
        self.chat_history_dir = self.base_dir / "chat_history"

    def ensure_dirs(self) -> None:
        """Create session directories if they don't exist."""
        for d in [self.base_dir, self.survey_cache_dir, self.analysis_cache_dir, self.chat_history_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_meta(self, meta: SessionMeta) -> None:
        self.ensure_dirs()
        self.meta_path.write_text(meta.model_dump_json(indent=2))

    def load_meta(self) -> SessionMeta:
        if self.meta_path.exists():
            data = json.loads(self.meta_path.read_text())
            return SessionMeta.model_validate(data)
        return SessionMeta()

    def save_survey_cache(self, repo_name: str, data: dict) -> None:
        """Save serialized survey bundle for a repo."""
        self.ensure_dirs()
        path = self.survey_cache_dir / f"{repo_name}.json"
        path.write_text(json.dumps(data, indent=2, default=str))

    def load_survey_cache(self, repo_name: str) -> dict | None:
        path = self.survey_cache_dir / f"{repo_name}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def append_chat_message(self, repo_name: str, message: ChatMessage) -> None:
        """Append a chat message to the repo's JSONL history."""
        self.ensure_dirs()
        path = self.chat_history_dir / f"{repo_name}.jsonl"
        with path.open("a") as f:
            f.write(message.model_dump_json() + "\n")

    def load_chat_history(self, repo_name: str) -> list[ChatMessage]:
        """Load all chat messages for a repo."""
        path = self.chat_history_dir / f"{repo_name}.jsonl"
        if not path.exists():
            return []

        messages = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                messages.append(ChatMessage.model_validate_json(line))
        return messages

    def clear_chat_history(self, repo_name: str) -> None:
        path = self.chat_history_dir / f"{repo_name}.jsonl"
        if path.exists():
            path.unlink()
