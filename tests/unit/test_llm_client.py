"""Unit tests for LLMClient with injected completion function."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from retui.llm.client import LLMClient
from retui.session.config import LLMConfig


def _make_response(content: str) -> SimpleNamespace:
    """Build a fake completion response matching the OpenAI response shape."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _make_stream_chunks(texts: list[str]) -> list[SimpleNamespace]:
    """Build fake streaming chunks matching the OpenAI streaming shape."""
    return [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])
        for text in texts
    ]


class TestLLMClientChat:
    def test_chat_sends_correct_args(self) -> None:
        captured = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return _make_response("Hello!")

        config = LLMConfig(model="openai/gpt-4o")
        client = LLMClient(config, completion_fn=fake_completion)

        result = client.chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful.",
            max_tokens=512,
        )

        assert result == "Hello!"
        assert captured["model"] == "openai/gpt-4o"
        assert captured["max_tokens"] == 512
        assert captured["messages"][0] == {
            "role": "system",
            "content": "You are helpful.",
        }
        assert captured["messages"][1] == {"role": "user", "content": "Hi"}

    def test_chat_without_system_prompt(self) -> None:
        captured = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return _make_response("Response")

        config = LLMConfig()
        client = LLMClient(config, completion_fn=fake_completion)

        result = client.chat(messages=[{"role": "user", "content": "Hi"}])

        assert result == "Response"
        assert len(captured["messages"]) == 1
        assert captured["messages"][0]["role"] == "user"

    def test_chat_empty_choices_returns_empty_string(self) -> None:
        def fake_completion(**kwargs):
            return SimpleNamespace(choices=[])

        client = LLMClient(LLMConfig(), completion_fn=fake_completion)
        result = client.chat(messages=[{"role": "user", "content": "Hi"}])

        assert result == ""

    def test_chat_none_content_returns_empty_string(self) -> None:
        def fake_completion(**kwargs):
            return _make_response(None)

        client = LLMClient(LLMConfig(), completion_fn=fake_completion)
        result = client.chat(messages=[{"role": "user", "content": "Hi"}])

        assert result == ""


class TestLLMClientChatStream:
    def test_chat_stream_yields_chunks(self) -> None:
        chunks = _make_stream_chunks(["Hello", " ", "world!"])

        def fake_completion(**kwargs):
            assert kwargs["stream"] is True
            return iter(chunks)

        config = LLMConfig(model="anthropic/claude-sonnet-4-20250514")
        client = LLMClient(config, completion_fn=fake_completion)

        result = list(
            client.chat_stream(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="Be brief.",
            )
        )

        assert result == ["Hello", " ", "world!"]

    def test_chat_stream_skips_empty_deltas(self) -> None:
        chunks = _make_stream_chunks(["Hello", "", "world!"])

        def fake_completion(**kwargs):
            return iter(chunks)

        client = LLMClient(LLMConfig(), completion_fn=fake_completion)
        result = list(client.chat_stream(messages=[{"role": "user", "content": "Hi"}]))

        assert result == ["Hello", "world!"]

    def test_chat_stream_without_system_prompt(self) -> None:
        captured = {}

        def fake_completion(**kwargs):
            captured.update(kwargs)
            return iter(_make_stream_chunks(["OK"]))

        client = LLMClient(LLMConfig(), completion_fn=fake_completion)
        list(client.chat_stream(messages=[{"role": "user", "content": "Hi"}]))

        assert len(captured["messages"]) == 1
        assert captured["messages"][0]["role"] == "user"
