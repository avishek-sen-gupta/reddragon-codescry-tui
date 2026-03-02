"""Pydantic models for repos.json configuration."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class RepoConfig(BaseModel):
    """Single repository entry."""

    name: str
    path: str
    languages: list[str] = Field(default_factory=list)
    auto_survey: bool = False
    exclude_files: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    """LLM provider settings (uses LiteLLM provider/model format)."""

    model: str = "anthropic/claude-sonnet-4-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"


class EmbeddingConfig(BaseModel):
    """BGE embedding concretisation settings."""

    enabled: bool = True
    model: str = "BAAI/bge-base-en-v1.5"
    device: str = "cpu"
    threshold: float = 0.62
    cache_path: str = ""


class Neo4jConfig(BaseModel):
    """Optional Neo4j graph database settings."""

    enabled: bool = False
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password_env: str = "NEO4J_PASSWORD"


class AppConfig(BaseModel):
    """Root configuration loaded from repos.json."""

    version: int = 1
    repos: list[RepoConfig] = Field(default_factory=list)
    session_dir: str = "~/.rev-eng-tui/sessions"
    proleap_bridge_jar: str = ""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)

    @property
    def session_path(self) -> Path:
        return Path(self.session_dir).expanduser()

    @classmethod
    def load(cls, path: str | Path) -> AppConfig:
        """Load config from a JSON file."""
        p = Path(path).expanduser().resolve()
        data = json.loads(p.read_text())
        return cls.model_validate(data)
