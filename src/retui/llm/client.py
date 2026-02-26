"""Claude API wrapper using the anthropic SDK."""

from __future__ import annotations

import os
from typing import Generator

from retui.session.config import LLMConfig


class LLMClient:
    """Wraps anthropic.Anthropic for Claude API calls."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic

            api_key = os.environ.get(self.config.api_key_env)
            if not api_key:
                raise RuntimeError(
                    f"API key not found. Set {self.config.api_key_env} environment variable."
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat request and return the assistant's response."""
        client = self._get_client()

        kwargs = {
            "model": self.config.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text if response.content else ""

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream a chat response, yielding text chunks."""
        client = self._get_client()

        kwargs = {
            "model": self.config.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
