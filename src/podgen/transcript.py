"""Transcript generation via a pluggable LLM backend.

The prompts live in ``src/podgen/prompts/*.md`` so users can also copy them
into Claude/ChatGPT for manual transcript generation (then feed the result
back through ``--from-transcript`` for TTS).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import prompts
from .llm import LLMClient

WORDS_PER_MINUTE = 150

SYSTEM_PROMPT = prompts.load("transcript_system")
_USER_PROMPT_TEMPLATE = prompts.load("transcript_user")


@dataclass
class Turn:
    speaker: str  # "A" or "B"
    text: str


def _build_user_prompt(source_text: str, guidance: str, duration_min: int, speaker_a: str, speaker_b: str) -> str:
    target_words = duration_min * WORDS_PER_MINUTE
    return _USER_PROMPT_TEMPLATE.format(
        speaker_a=speaker_a,
        speaker_b=speaker_b,
        target_words=target_words,
        duration_min=duration_min,
        words_per_minute=WORDS_PER_MINUTE,
        guidance=guidance or "(none - use your judgment)",
        source_text=source_text,
    )


def generate_transcript(
    client: LLMClient,
    source_text: str,
    guidance: str,
    duration_min: int,
    speaker_a: str = "Alex",
    speaker_b: str = "Jordan",
    max_tokens: int = 16000,
    on_chunk=None,
) -> str:
    user_prompt = _build_user_prompt(source_text, guidance, duration_min, speaker_a, speaker_b)
    return client.complete(system=SYSTEM_PROMPT, user=user_prompt, max_tokens=max_tokens, on_chunk=on_chunk)


_TURN_RE = re.compile(r"^SPEAKER_([AB])\s*:\s*(.*)$", re.IGNORECASE)


def parse_transcript(raw: str) -> list[Turn]:
    turns: list[Turn] = []
    current: Turn | None = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            if current:
                current.text += "\n"
            continue
        m = _TURN_RE.match(line)
        if m:
            if current and current.text.strip():
                current.text = current.text.strip()
                turns.append(current)
            current = Turn(speaker=m.group(1).upper(), text=m.group(2).strip())
        elif current:
            current.text += " " + line
    if current and current.text.strip():
        current.text = current.text.strip()
        turns.append(current)
    return turns
