"""Windows-friendly PATH augmentation for espeak-ng and ffmpeg.

winget installs these tools but PATH updates don't apply to existing shells.
We probe common install locations and add them to this process's PATH so
Kokoro (espeak-ng) and pydub (ffmpeg) can find them.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _candidates_espeak() -> list[Path]:
    prog_files = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ]
    return [Path(p) / "eSpeak NG" for p in prog_files if p]


def _candidates_ffmpeg() -> list[Path]:
    paths: list[Path] = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        winget_root = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.exists():
            for pkg in winget_root.glob("Gyan.FFmpeg*"):
                for sub in pkg.glob("ffmpeg-*"):
                    bin_dir = sub / "bin"
                    if bin_dir.exists():
                        paths.append(bin_dir)
    return paths


def ensure_tools_on_path() -> None:
    """Idempotently prepend known install dirs to PATH on Windows."""
    if sys.platform != "win32":
        return
    extras: list[Path] = []
    for d in _candidates_espeak() + _candidates_ffmpeg():
        if d.exists() and str(d) not in os.environ.get("PATH", ""):
            extras.append(d)
    if extras:
        os.environ["PATH"] = os.pathsep.join(str(p) for p in extras) + os.pathsep + os.environ.get("PATH", "")

    # Set PHONEMIZER_ESPEAK_LIBRARY hint for phonemizer/misaki if DLL is in eSpeak NG dir
    if not os.environ.get("PHONEMIZER_ESPEAK_LIBRARY"):
        for d in _candidates_espeak():
            dll = d / "libespeak-ng.dll"
            if dll.exists():
                os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = str(dll)
                break
