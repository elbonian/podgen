"""Transcript generation via Anthropic Claude."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .llm import LLMClient

WORDS_PER_MINUTE = 150

SYSTEM_PROMPT = """You are a podcast scriptwriter. You write natural, engaging two-speaker \
podcast dialogue based on source material the user provides.

Rules:
- Output ONLY the transcript, no preamble, no outline, no stage directions in brackets.
- Every line must start with either "SPEAKER_A:" or "SPEAKER_B:" (exact prefix).
- Alternate speakers naturally. Keep turns mostly 1-4 sentences; occasional longer turns are fine.
- Write in a conversational tone: contractions, reactions ("yeah", "right", "huh"), short asides.
- Do NOT include non-verbal cues like [laughs] or *sighs* - the TTS can't handle them.
- Do NOT include sound effects, music cues, or chapter markers.
- Cover the source material accurately; do not fabricate facts.
- Aim for approximately the target word count the user specifies."""


@dataclass
class Turn:
    speaker: str  # "A" or "B"
    text: str


def _build_user_prompt(source_text: str, guidance: str, duration_min: int, speaker_a: str, speaker_b: str) -> str:
    target_words = duration_min * WORDS_PER_MINUTE
    return f"""Generate a two-speaker podcast transcript from the source material below.

SPEAKER_A is named "{speaker_a}". SPEAKER_B is named "{speaker_b}". They do NOT need to say their \
names repeatedly; just converse naturally.

Target length: approximately {target_words} words (~{duration_min} minutes of spoken audio at {WORDS_PER_MINUTE} wpm).

User guidance / focus:
{guidance or "(none - use your judgment)"}

Source material:
{source_text}

Now write the full transcript. Remember: every line must start with "SPEAKER_A:" or "SPEAKER_B:"."""


def generate_transcript(
    client: LLMClient,
    source_text: str,
    guidance: str,
    duration_min: int,
    speaker_a: str = "Alex",
    speaker_b: str = "Jordan",
    max_tokens: int = 16000,
) -> str:
    user_prompt = _build_user_prompt(source_text, guidance, duration_min, speaker_a, speaker_b)
    return client.complete(system=SYSTEM_PROMPT, user=user_prompt, max_tokens=max_tokens)


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
