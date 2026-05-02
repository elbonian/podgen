"""LLM backend abstraction: Anthropic or OpenAI-compatible (LM Studio, Ollama, etc.)."""
from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str, max_tokens: int) -> str: ...


class AnthropicClient:
    def __init__(self, model: str):
        from anthropic import Anthropic

        self.model = model
        self.client = Anthropic()

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()


class OpenAICompatibleClient:
    """Works with LM Studio, Ollama, vLLM, any OpenAI-compatible /v1 endpoint."""

    def __init__(self, model: str, base_url: str, api_key: str | None = None):
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key or "not-needed")

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()


def build_client(backend: str, model: str, base_url: str | None = None) -> LLMClient:
    backend = backend.lower()
    if backend == "anthropic":
        return AnthropicClient(model=model)
    if backend in {"lmstudio", "openai", "openai-compatible"}:
        url = base_url or os.getenv("OPENAI_BASE_URL") or "http://localhost:1234/v1"
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAICompatibleClient(model=model, base_url=url, api_key=api_key)
    raise ValueError(f"Unknown backend: {backend!r}. Use 'anthropic' or 'lmstudio'.")
