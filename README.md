# podgen v1.0

**A local, open-source alternative to Google NotebookLM's podcast feature.** Point it at a folder of documents, get a natural two-speaker podcast — transcript and audio — generated on your own machine.

- **Transcript**: Claude (Anthropic API) or any OpenAI-compatible local server (LM Studio, Ollama, vLLM, llama.cpp, text-generation-webui)
- **Audio**: [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) running locally — no cloud TTS costs
- **Cost**: $0 fully local, or pennies if you use Claude for the transcript

## Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

## Quick Start

```cmd
:: Generate a 5-minute podcast from documents in .\test using LM Studio
.\.venv\Scripts\podgen.exe -s .\test -d 5 --backend lmstudio --model "openai/gpt-oss-20b"

:: Or with Anthropic Claude (needs ANTHROPIC_API_KEY in .env)
.\.venv\Scripts\podgen.exe -s .\test -d 5 --backend anthropic --model claude-sonnet-4-5
```

Outputs in `.\output\`:
- `transcript.md` — raw two-speaker script
- `transcript.json` — parsed turns
- `podcast.mp3` — final audio

## Requirements

- **Python 3.10, 3.11, or 3.12** (Kokoro does not yet support 3.13)
- **Windows, macOS, or Linux**
- **espeak-ng** — phonemizer used by Kokoro
- **ffmpeg** — mp3 export via pydub
- One of:
  - **LM Studio** (or Ollama / vLLM / llama.cpp) running locally with a chat model loaded
  - An **Anthropic API key**

Optional but recommended:
- **GPU** — Kokoro runs on CPU fine but is faster on CUDA; local LLMs strongly benefit from GPU

## Installation

### 1. System dependencies

**Windows (winget):**

```cmd
winget install eSpeak-NG.eSpeak-NG
winget install Gyan.FFmpeg
winget install Python.Python.3.12
```

**macOS:**

```bash
brew install espeak-ng ffmpeg python@3.12
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt install espeak-ng ffmpeg python3.12 python3.12-venv
```

> On Windows, `podgen` automatically locates espeak-ng and ffmpeg from their winget install paths — no manual PATH setup required. See `@src/podgen/platform_paths.py`.

### 2. Python package

```cmd
py -3.12 -m venv .venv
.\.venv\Scripts\activate.bat
pip install -e .
```

(Or use `Activate.ps1` in PowerShell.)

### 3. Configure API keys (optional)

```cmd
copy .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Not needed if you're using LM Studio / a local backend exclusively.

### 4. First run

The first Kokoro invocation downloads ~330 MB of model weights from Hugging Face into your user cache.

## Usage

### Basic

```cmd
podgen -s <source-folder> -d <minutes> [options]
```

### All Options

| Flag | Default | Description |
|---|---|---|
| `-s, --source-dir` | — | Folder of documents (`.txt`, `.md`, `.pdf`). Recursive. |
| `-o, --output-dir` | `output` | Where to write transcript + audio |
| `-d, --duration` | `5` | Target minutes of spoken audio (1–60) |
| `-g, --guidance` | `""` | Tone/focus prompt, e.g. "focus on the core argument" |
| `--speaker-a` / `--speaker-b` | `Alex` / `Jordan` | Names used in the script |
| `--voice-a` / `--voice-b` | `af_heart` / `am_michael` | Kokoro voice IDs (see [Voices](docs/VOICES.md)) |
| `--backend` | `anthropic` | `anthropic` or `lmstudio` |
| `--model` | `claude-sonnet-4-5` | Model ID for the chosen backend |
| `--base-url` | `http://localhost:1234/v1` | Override OpenAI-compatible endpoint |
| `--format` | `mp3` | `mp3` or `wav` |
| `--transcript-only` | off | Skip TTS |
| `--from-transcript <file>` | — | Skip LLM, synthesize audio from an existing `transcript.md` |

### Recipes

**Local stack (zero cost):**

```cmd
podgen -s .\docs -d 10 --backend lmstudio --model "openai/gpt-oss-20b" ^
  -g "Deep dive for intermediate audience"
```

**High-quality transcript via Claude:**

```cmd
podgen -s .\docs -d 10 --backend anthropic --model claude-sonnet-4-5
```

**British voice pair:**

```cmd
podgen -s .\docs -d 5 --voice-a bf_emma --voice-b bm_george
```

**Iterate on voices without re-running the LLM:**

```cmd
podgen --from-transcript .\output\transcript.md -o .\output ^
  --voice-a af_bella --voice-b bm_lewis
```

**Transcript-only (review before synthesizing):**

```cmd
podgen -s .\docs -d 5 --transcript-only --backend lmstudio --model "openai/gpt-oss-20b"
```

**Different local server (Ollama):**

```cmd
podgen -s .\docs --backend lmstudio --base-url http://localhost:11434/v1 --model llama3.1:70b
```

## Documentation

Detailed docs live in `docs/`:

- **`docs/ARCHITECTURE.md`** — pipeline internals, module responsibilities
- **`docs/BACKENDS.md`** — LLM backend configuration, adding new providers
- **`docs/VOICES.md`** — full Kokoro voice catalog with guidance
- **`docs/TROUBLESHOOTING.md`** — common errors and fixes
- **`docs/PROMPTING.md`** — how to write effective `--guidance`

## How It Works

```
┌─────────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐
│ Source dir  │──▶│  ingest  │──▶│   LLM   │──▶│   TTS   │──▶│  stitch  │
│ .txt .md    │   │ pypdf +  │   │ Claude  │   │ Kokoro  │   │ + norm.  │
│ .pdf        │   │ text rd. │   │ or local│   │  82M    │   │  → mp3   │
└─────────────┘   └──────────┘   └─────────┘   └─────────┘   └──────────┘
                                      │
                                      ▼
                               SPEAKER_A: ...
                               SPEAKER_B: ...
```

1. **Ingest** (`@src/podgen/ingest.py`): recursively loads `.txt`/`.md`/`.pdf` from the source folder, concatenates with filename headers, truncates at 120k chars as a budget guard.
2. **Transcript** (`@src/podgen/transcript.py`): sends the corpus to the configured LLM with a strict system prompt requiring `SPEAKER_A:` / `SPEAKER_B:` line prefixes. Target length = `duration × 150 wpm`.
3. **Parse** (`parse_transcript`): regex-extracts turns into a list of `Turn(speaker, text)` objects.
4. **TTS** (`@src/podgen/tts.py`): for each turn, selects `voice_a` or `voice_b` and synthesizes audio via Kokoro. Long turns are split at sentence boundaries (~400 chars) for stable output.
5. **Stitch** (`@src/podgen/assemble.py`): concatenates per-turn audio with 350 ms silences, peak-normalizes to -1 dBFS, exports via `soundfile` (wav) or `pydub` → `ffmpeg` (mp3).

For full architecture details see `@docs/ARCHITECTURE.md`.

## Troubleshooting

Quick reference — see `@docs/TROUBLESHOOTING.md` for the full list.

- **`BadRequestError: n_keep > n_ctx`** — your LM Studio model's context window is smaller than the input. Raise context length in LM Studio's model settings, or shrink the source.
- **`FileNotFoundError: [WinError 2]`** during TTS — espeak-ng or ffmpeg not found. Reinstall via winget; podgen will auto-locate them. Restart your shell if freshly installed.
- **`Could not find a version that satisfies the requirement kokoro>=0.9.2`** — you're on Python 3.13. Use 3.10–3.12 instead.
- **Notepad opens when running `Activate.ps1`** — you're in `cmd`, not PowerShell. Use `activate.bat` or call `.\.venv\Scripts\podgen.exe` directly.

## Roadmap

Planned for v1.1+:

- Per-document summarization for large corpora (currently truncates)
- Markdown cleanup pass (strip nav/boilerplate from web-scraped `.md`)
- Segment caching (don't re-synthesize unchanged turns)
- Additional ingestors: `.docx`, `.html`, `.pptx`, URLs
- Optional Chatterbox / F5-TTS backends for voice cloning
- Intro/outro music support
- Simple FastAPI web UI
- Streaming transcript generation with live progress

## License

MIT. Kokoro-82M is Apache 2.0. Check individual model licenses if you use other LLM backends.

## Credits

- **[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)** by `@hexgrad` — the TTS model that makes this actually sound good.
- **Anthropic Claude** — excellent transcript quality.
- **LM Studio / Ollama / llama.cpp** — local LLM infrastructure.
