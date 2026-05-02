"""Stitch per-turn audio into a single podcast file."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .tts import SAMPLE_RATE


def _silence(seconds: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    return np.zeros(int(seconds * sample_rate), dtype=np.float32)


def stitch(
    segments: list[np.ndarray],
    output_path: Path,
    gap_seconds: float = 0.35,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Concatenate segments with small silent gaps. Writes wav or mp3 via extension."""
    if not segments:
        raise ValueError("No audio segments to stitch.")

    gap = _silence(gap_seconds, sample_rate)
    pieces: list[np.ndarray] = []
    for i, seg in enumerate(segments):
        if seg.size == 0:
            continue
        pieces.append(seg)
        if i != len(segments) - 1:
            pieces.append(gap)
    full = np.concatenate(pieces)

    # Peak normalize to -1 dBFS
    peak = float(np.max(np.abs(full))) or 1.0
    full = full * (0.891 / peak)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".mp3":
        # soundfile can't write mp3 on all platforms; go via pydub
        from pydub import AudioSegment

        int16 = np.clip(full * 32767, -32768, 32767).astype(np.int16)
        seg = AudioSegment(
            int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1,
        )
        seg.export(str(output_path), format="mp3", bitrate="128k")
    else:
        sf.write(str(output_path), full, sample_rate)
