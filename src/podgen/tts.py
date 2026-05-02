"""Kokoro TTS wrapper."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import soundfile as sf

SAMPLE_RATE = 24_000  # Kokoro default


def _split_sentences(text: str, max_chars: int = 400) -> list[str]:
    """Split long turns into sentence-ish chunks for stable TTS."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        if len(buf) + len(p) + 1 <= max_chars:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks or [text]


class KokoroTTS:
    """Lazy-loaded Kokoro pipeline. Generates audio for a given speaker voice."""

    def __init__(self, lang_code: str = "a"):
        # 'a' = American English, 'b' = British English
        from kokoro import KPipeline  # local import: heavy deps

        self.pipeline = KPipeline(lang_code=lang_code)

    def synth(self, text: str, voice: str, speed: float = 1.0) -> np.ndarray:
        audio_parts: list[np.ndarray] = []
        for chunk in _split_sentences(text):
            generator = self.pipeline(chunk, voice=voice, speed=speed)
            for _gs, _ps, audio in generator:
                if audio is None:
                    continue
                arr = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
                audio_parts.append(arr.astype(np.float32))
        if not audio_parts:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(audio_parts)


def save_wav(path: Path, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    sf.write(str(path), audio, sample_rate)
