"""LLM backend abstraction: Anthropic or OpenAI-compatible (LM Studio, Ollama, etc.).

All clients stream responses by default. Streaming avoids HTTP read-timeout
issues with slow local models on long generations and provides live progress.
"""
from __future__ import annotations

import os
import sys
from typing import Callable, Protocol

# Generous default timeout for slow local models; streaming makes this rarely matter.
DEFAULT_TIMEOUT_S = 60 * 30  # 30 minutes


ProgressFn = Callable[[str], None]


def _default_progress(chunk: str) -> None:
    sys.stdout.write(chunk)
    sys.stdout.flush()


class LLMClient(Protocol):
    def complete(self, system: str, user: str, max_tokens: int, on_chunk: ProgressFn | None = ...) -> str: ...


class AnthropicClient:
    def __init__(self, model: str, timeout: float = DEFAULT_TIMEOUT_S):
        from anthropic import Anthropic

        self.model = model
        self.client = Anthropic(timeout=timeout)

    def complete(self, system: str, user: str, max_tokens: int, on_chunk: ProgressFn | None = None) -> str:
        chunks: list[str] = []
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for piece in stream.text_stream:
                if not piece:
                    continue
                chunks.append(piece)
                if on_chunk:
                    on_chunk(piece)
        return "".join(chunks).strip()


class OpenAICompatibleClient:
    """Works with LM Studio, Ollama, vLLM, any OpenAI-compatible /v1 endpoint."""

    def __init__(self, model: str, base_url: str, api_key: str | None = None, timeout: float = DEFAULT_TIMEOUT_S):
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key or "not-needed", timeout=timeout)

    def complete(self, system: str, user: str, max_tokens: int, on_chunk: ProgressFn | None = None) -> str:
        stream = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            stream=True,
        )
        chunks: list[str] = []
        for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta.content
            if not delta:
                continue
            chunks.append(delta)
            if on_chunk:
                on_chunk(delta)
        return "".join(chunks).strip()


def build_client(backend: str, model: str, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT_S) -> LLMClient:
    backend = backend.lower()
    if backend == "anthropic":
        return AnthropicClient(model=model, timeout=timeout)
    if backend in {"lmstudio", "openai", "openai-compatible"}:
        url = base_url or os.getenv("OPENAI_BASE_URL") or "http://localhost:1234/v1"
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAICompatibleClient(model=model, base_url=url, api_key=api_key, timeout=timeout)
    raise ValueError(f"Unknown backend: {backend!r}. Use 'anthropic' or 'lmstudio'.")
