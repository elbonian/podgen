# Troubleshooting

## Install / Setup

### `Could not find a version that satisfies the requirement kokoro>=0.9.2`

**Cause**: You're on Python 3.13. Kokoro currently requires 3.10–3.12.

**Fix**:

```cmd
winget install Python.Python.3.12
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\activate.bat
pip install -e .
```

### Notepad opens when running `Activate.ps1`

**Cause**: You're in `cmd.exe`, not PowerShell. `cmd` doesn't know how to execute `.ps1` files.

**Fix**: Use the cmd-compatible activator, or skip activation:

```cmd
.\.venv\Scripts\activate.bat

:: Or just call the exe directly, no venv activation needed:
.\.venv\Scripts\podgen.exe -s .\docs
```

### `winget` adds espeak-ng/ffmpeg to PATH but shell can't find them

**Cause**: winget updates the *User* PATH environment variable, but existing shell sessions inherited their PATH at launch.

**Fix**: podgen automatically discovers espeak-ng (at `C:\Program Files\eSpeak NG\`) and ffmpeg (at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\...\bin\`) — see `@src/podgen/platform_paths.py`. If they're installed but not found:

```cmd
:: Confirm install locations:
Test-Path "C:\Program Files\eSpeak NG\espeak-ng.exe"
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter ffmpeg.exe -Recurse | Select-Object -First 1
```

If these return nothing, re-run the `winget install` commands. If they return paths but podgen still can't find them, open a new shell (PATH changes apply on shell start).

## Runtime Errors

### `BadRequestError: The number of tokens to keep from the initial prompt is greater than the context length (n_keep: X >= n_ctx: Y)`

**Cause**: Your LM Studio model was loaded with a context window smaller than the input size. Example: Wikipedia markdown dumps contain lots of navigation boilerplate that inflates token count.

**Fixes** (in order of preference):

1. **Raise the LM Studio context window**: go to **My Models** → your model → gear icon → **Context Length** → set to `32768` or higher. Reload the model. Most modern models support 128k+.
2. **Use a different (longer-context) model** temporarily.
3. **Shrink the source**: remove boilerplate-heavy files from the source folder, or clean `.md` files manually before ingest.

### `FileNotFoundError: [WinError 2] The system cannot find the file specified` during TTS load

**Cause**: espeak-ng not found. `@src/podgen/platform_paths.py` couldn't locate it.

**Fix**: verify the install path:

```cmd
dir "C:\Program Files\eSpeak NG\espeak-ng.exe"
```

If missing, reinstall: `winget install eSpeak-NG.eSpeak-NG`.

### `AttributeError: 'NoneType' object has no attribute 'exists'`

**Cause**: Ran `podgen` without `--source-dir` and without `--from-transcript`.

**Fix**: pass one or the other. Fixed in v1.0 with a clean error message.

### `Failed to parse any SPEAKER_A/SPEAKER_B turns from transcript`

**Cause**: The LLM didn't follow the `SPEAKER_A:` / `SPEAKER_B:` format.

**Fixes**:
- Small local models sometimes ignore formatting rules. Switch to a larger model (14B+) or Claude.
- Check `output/transcript.md` to see what the LLM actually produced. If it's close but e.g. uses `**Alex:**` instead, the regex in `@src/podgen/transcript.py:62` can be extended.
- Retry — LLMs are non-deterministic.

### `podcast.mp3` is 0 bytes / empty

**Cause**: TTS stage failed silently. Check stderr for the real error — typically espeak-ng or ffmpeg missing.

## Output Quality

### Transcript is too short / too long

- `--duration` targets a word count assuming 150 wpm. Actual spoken length varies ±20% depending on voice and content complexity.
- Very small models may ignore the target entirely. Use a larger model.

### Voices sound too similar

- Swap to a British + American mix, e.g. `--voice-a af_heart --voice-b bm_george`.
- See `@docs/VOICES.md` for all pairings.

### Audio has clicks/pops between turns

- The default 0.35 s silence between turns is usually enough. If you hear clicks, check that your input text doesn't have unusual characters (em-dashes, smart quotes, etc. — Kokoro usually handles them but edge cases exist).

### Audio is clipping / too loud

- v1.0 peak-normalizes to -1 dBFS. If you need more headroom, adjust the `0.891` constant in `@src/podgen/assemble.py:32` (0.708 = -3 dBFS, 0.5 = -6 dBFS).

### Kokoro mispronounces proper nouns

- espeak-ng fallback is used for unknown words and can produce odd phonemes. Workarounds:
  - Replace rare proper nouns with a phonetic spelling in the transcript, then use `--from-transcript`.
  - For the F Prime example: "F Prime" → "Eff Prime" renders better.

## Performance

### Kokoro is slow on my machine

- First run downloads ~330 MB from HuggingFace — subsequent runs load from cache.
- CPU inference: ~0.3× real-time on modern CPUs is typical. GPU (CUDA) is 3–5× real-time.
- A 5-minute podcast with ~13 turns takes ~45 s on a decent GPU, 2–3 min on CPU.

### Local LLM is slow

- Smaller models help: Qwen 2.5 7B finishes transcripts in ~30 s vs 3 min for 72B variants.
- GPU offload: in LM Studio, max out GPU layers for your VRAM.
- Enable flash attention if supported.

### HuggingFace download is slow

- Set `HF_TOKEN` env var to authenticate (higher rate limits).
- Use a mirror: set `HF_ENDPOINT=https://hf-mirror.com` if you're in a rate-limited region.

## Still Stuck?

Useful debugging commands:

```cmd
:: What does podgen think its PATH looks like?
.\.venv\Scripts\python.exe -c "from podgen.platform_paths import ensure_tools_on_path; ensure_tools_on_path(); import os; print(os.environ['PATH'])"

:: Test Kokoro in isolation:
.\.venv\Scripts\python.exe -c "from podgen.platform_paths import ensure_tools_on_path; ensure_tools_on_path(); from podgen.tts import KokoroTTS; t = KokoroTTS(); a = t.synth('Test.', voice='af_heart'); print(a.shape)"

:: Test LM Studio reachability:
curl http://localhost:1234/v1/models

:: Run with Python traceback for deeper errors:
.\.venv\Scripts\python.exe -m podgen.cli -s .\test -d 2 --backend lmstudio --model "your-model"
```
