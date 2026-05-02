# Changelog

All notable changes to podgen are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-05-01

Initial release.

### Added
- Document ingestion for `.txt`, `.md`, `.pdf` (recursive folder scan).
- Two LLM backend implementations:
  - `AnthropicClient` — Claude via the official `anthropic` SDK.
  - `OpenAICompatibleClient` — works with LM Studio, Ollama, vLLM, llama.cpp, text-generation-webui, and OpenAI itself.
- Two-speaker transcript generation with strict `SPEAKER_A:` / `SPEAKER_B:` formatting and word-budget targeting (150 wpm × duration).
- Kokoro-82M TTS integration with sentence-level chunking for stable synthesis.
- Audio stitching with configurable inter-turn silences, peak normalization, and mp3/wav export.
- Typer-based CLI with rich progress indicators.
- `--from-transcript` mode to skip the LLM and re-synthesize audio from an existing transcript.
- `--transcript-only` mode to generate text without running TTS.
- Automatic Windows PATH augmentation for espeak-ng and ffmpeg (`src/podgen/platform_paths.py`).
- `.env` support via `python-dotenv` for API keys.

### Documentation
- Comprehensive `README.md`.
- `docs/ARCHITECTURE.md` — pipeline and module internals.
- `docs/BACKENDS.md` — LLM backend configuration reference.
- `docs/VOICES.md` — Kokoro voice catalog.
- `docs/TROUBLESHOOTING.md` — known issues and fixes.
- `docs/PROMPTING.md` — guidance on writing effective `--guidance`.
