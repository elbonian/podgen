# Architecture

podgen is a linear five-stage pipeline wired together by `@src/podgen/cli.py`. Each stage is a separate module with a single responsibility, so you can replace or extend any one of them without touching the others.

## Pipeline

```
         ┌────────────────────────────────────────────────────────────┐
         │                         cli.py                              │
         │  (Typer command, orchestration, progress reporting)         │
         └──────┬─────────┬─────────┬──────────┬──────────┬────────────┘
                │         │         │          │          │
                ▼         ▼         ▼          ▼          ▼
         ┌──────────┐ ┌──────┐ ┌─────────┐ ┌──────┐ ┌──────────┐
         │ ingest   │ │ llm  │ │transcr. │ │ tts  │ │ assemble │
         │ .py      │ │ .py  │ │  .py    │ │ .py  │ │  .py     │
         └──────────┘ └──────┘ └─────────┘ └──────┘ └──────────┘
```

## Module Responsibilities

### `ingest.py`

- **Purpose**: turn a folder of heterogeneous documents into a single text blob.
- **Public API**: `load_folder(Path) -> list[(name, text)]`, `combine_docs(docs, max_chars) -> str`.
- **Supported formats**: `.txt`, `.md` via plain file read; `.pdf` via `pypdf.PdfReader`.
- **Design notes**:
  - Recurses the folder, sorted order for reproducibility.
  - Silent per-file error handling — one bad PDF shouldn't kill the run.
  - `combine_docs` caps at 120k chars as a naive token-budget guard. Long corpora are truncated; a future summarization pass will replace this.
- **File**: `@src/podgen/ingest.py`

### `llm.py`

- **Purpose**: pluggable chat-completion abstraction.
- **Public API**: `build_client(backend, model, base_url) -> LLMClient` where `LLMClient` is a `Protocol` with a single `complete(system, user, max_tokens) -> str` method.
- **Implementations**:
  - `AnthropicClient` — wraps `anthropic.Anthropic().messages.create(...)`.
  - `OpenAICompatibleClient` — wraps `openai.OpenAI(base_url=...)` against any `/v1/chat/completions` endpoint.
- **Why a Protocol, not a base class**: structural typing keeps new backends minimal; a backend is "just an object with a `.complete()` method."
- **File**: `@src/podgen/llm.py`

### `transcript.py`

- **Purpose**: generate and parse two-speaker dialogue.
- **Key constants**: `WORDS_PER_MINUTE = 150` drives the target word count passed to the LLM.
- **System prompt** (`SYSTEM_PROMPT`): hard rules forcing `SPEAKER_A:` / `SPEAKER_B:` prefixes, conversational tone, no stage directions (TTS can't voice them), no hallucinated facts.
- **User prompt** (`_build_user_prompt`): embeds source text, user guidance, speaker names, and the target word count.
- **Parser** (`parse_transcript`): regex `^SPEAKER_([AB])\s*:\s*(.*)$` (case-insensitive) with continuation-line support (non-prefixed lines append to the current turn).
- **Output model**: `Turn(speaker: "A"|"B", text: str)`.
- **File**: `@src/podgen/transcript.py`

### `tts.py`

- **Purpose**: synthesize audio for one turn at a time.
- **Public API**: `KokoroTTS().synth(text, voice, speed=1.0) -> np.ndarray` (float32 mono, 24 kHz).
- **Lazy loading**: the `kokoro` package + torch + model weights load only when `KokoroTTS()` is constructed — keeps CLI help fast and `--transcript-only` skip-friendly.
- **Chunking**: `_split_sentences` splits long turns into ≤400-char sentence-aligned pieces to avoid prosody drift in longer generations. Chunks are concatenated per turn.
- **Sample rate**: 24 kHz throughout the pipeline (Kokoro's native rate).
- **File**: `@src/podgen/tts.py`

### `assemble.py`

- **Purpose**: stitch per-turn audio into the final file.
- **Public API**: `stitch(segments, output_path, gap_seconds=0.35)`.
- **Processing**:
  1. Insert `gap_seconds` of silence between turns (not after the last one).
  2. Peak-normalize to -1 dBFS (`0.891` linear) to avoid clipping while staying loud.
  3. Export: wav via `soundfile.write`, mp3 via `pydub` → `ffmpeg`.
- **File**: `@src/podgen/assemble.py`

### `platform_paths.py`

- **Purpose**: Windows ergonomics — locate espeak-ng and ffmpeg from their winget install dirs and prepend to `os.environ["PATH"]`, plus set `PHONEMIZER_ESPEAK_LIBRARY`.
- **Why**: winget adds new install dirs to the User PATH, but existing shells don't inherit that until restart. This module closes that gap so `pip install + podgen` works in the same session.
- **No-op on non-Windows**.
- **File**: `@src/podgen/platform_paths.py`

### `cli.py`

- **Purpose**: CLI orchestration.
- **Framework**: Typer + Rich (progress bars, colored output).
- **Early side effect**: calls `ensure_tools_on_path()` before importing heavy modules to guarantee Kokoro/pydub can find their native deps.
- **Branches**:
  - `--from-transcript <path>` → skip ingest + LLM, go straight to TTS.
  - Otherwise: ingest → LLM → parse → TTS → stitch.
- **Exit codes**: `0` success, `1` no documents / missing args, `2` transcript parse failure.
- **File**: `@src/podgen/cli.py`

## Data Flow

```
folder of files
  │
  ▼
list[(filename, text)]                ← ingest.load_folder
  │
  ▼
str (combined, ≤120k chars)           ← ingest.combine_docs
  │
  ▼
str (raw transcript with SPEAKER_*)   ← transcript.generate_transcript
  │                                       (client.complete dispatches to
  │                                        Anthropic or OpenAI-compat)
  ▼
list[Turn]                            ← transcript.parse_transcript
  │
  ▼
list[np.ndarray] (per turn)           ← tts.KokoroTTS.synth per turn
  │
  ▼
output/podcast.mp3                    ← assemble.stitch
```

## Extension Points

- **New ingest format**: add a reader in `ingest.py`, extend the `SUPPORTED` set.
- **New LLM backend**: implement a class with `complete(system, user, max_tokens)` and a `build_client` branch.
- **New TTS backend**: create a sibling of `KokoroTTS` with the same `synth(text, voice)` signature; add a `--tts-backend` flag to `cli.py`.
- **Custom pipeline stages** (summarization, caching, intro music): insert between existing stages — they're independent functions.

## Non-Goals for v1

- Real-time streaming (batch only).
- Multi-speaker (3+) dialogue. Two speakers is the spec.
- Speaker emotion control beyond voice choice.
- Automatic source curation / web scraping. Bring your own documents.
