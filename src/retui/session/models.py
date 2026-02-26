"""Session data models for persistence."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionMeta(BaseModel):
    """Tracks the user's last navigation state."""

    last_screen: str = "dashboard"
    last_repo: str = ""
    last_file: str = ""
    last_function: str = ""
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class ChatMessage(BaseModel):
    """A single chat message for persistence."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
