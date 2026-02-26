"""LLM API wrapper using LiteLLM for multi-provider support."""

from __future__ import annotations

import logging
from typing import Callable, Generator

from retui.session.config import LLMConfig

logger = logging.getLogger(__name__)


def _default_completion(**kwargs):
    """Default completion function using litellm."""
    import litellm

    return litellm.completion(**kwargs)


class LLMClient:
    """Wraps LiteLLM completion for multi-provider LLM calls."""

    def __init__(
        self,
        config: LLMConfig,
        completion_fn: Callable = _default_completion,
    ) -> None:
        self.config = config
        self._completion_fn = completion_fn

    def _build_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> list[dict[str, str]]:
        """Prepend system prompt as a system message if provided."""
        if not system_prompt:
            return messages
        return [{"role": "system", "content": system_prompt}] + messages

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat request and return the assistant's response."""
        full_messages = self._build_messages(messages, system_prompt)

        logger.info("Sending chat request to model=%s", self.config.model)
        response = self._completion_fn(
            model=self.config.model,
            max_tokens=max_tokens,
            messages=full_messages,
        )

        content = response.choices[0].message.content if response.choices else ""
        return content or ""

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """Stream a chat response, yielding text chunks."""
        full_messages = self._build_messages(messages, system_prompt)

        logger.info("Starting streaming chat request to model=%s", self.config.model)
        response = self._completion_fn(
            model=self.config.model,
            max_tokens=max_tokens,
            messages=full_messages,
            stream=True,
        )

        for chunk in response:
            delta_content = chunk.choices[0].delta.content if chunk.choices else ""
            if delta_content:
                yield delta_content
