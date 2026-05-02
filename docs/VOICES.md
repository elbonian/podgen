# Kokoro Voices

Kokoro-82M ships a fixed set of preset voices. Each voice ID encodes:

- **First letter**: language (`a` = American English, `b` = British English, and others for additional languages).
- **Second letter**: gender (`f` = female, `m` = male).
- **Remainder**: the voice's name.

## Recommended Pairs for Two-Speaker Podcasts

Pairs with good contrast for the listener:

| Speaker A | Speaker B | Feel |
|---|---|---|
| `af_heart` | `am_michael` | Default — warm F + neutral M, American |
| `af_bella` | `am_adam` | Bright F + relaxed M, American |
| `af_nicole` | `am_onyx` | Energetic F + deeper M, American |
| `bf_emma` | `bm_george` | Classic British pair |
| `bf_isabella` | `bm_lewis` | British, younger-sounding |
| `af_sarah` | `bm_george` | Mixed accent — maximum distinction |
| `bf_emma` | `am_michael` | Mixed accent, warm |

## American English

### Female

- `af_heart` ★ — Warm, expressive. Great default.
- `af_bella` — Bright, upbeat.
- `af_nicole` — Energetic, clear.
- `af_sarah` — Softer, more measured.
- `af_sky` — Youthful.

### Male

- `am_michael` ★ — Neutral, mid-range. Great default.
- `am_adam` — Relaxed, conversational.
- `am_onyx` — Deeper, authoritative.
- `am_eric` — Mid-range, narrative.

## British English

### Female

- `bf_emma` — Classic RP, clear.
- `bf_isabella` — Softer, younger-sounding.
- `bf_alice` — Measured, news-reader quality.
- `bf_lily` — Warm, storyteller.

### Male

- `bm_george` — Deep, authoritative.
- `bm_lewis` — Mid-range, friendly.
- `bm_daniel` — Crisp, news-reader.
- `bm_fable` — Narrative, storyteller.

## Other Languages

Kokoro also ships voices for Japanese (`j*`), Mandarin (`z*`), Spanish (`e*`), French (`f*`), Hindi (`h*`), Italian (`i*`), and Portuguese (`p*`). podgen v1.0 defaults to American English (`lang_code='a'`); for other languages you'd need to modify `@src/podgen/tts.py:26` to pass the appropriate `lang_code`.

See the [official VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) for the complete list.

## Usage

```cmd
podgen -s .\docs --voice-a bf_emma --voice-b bm_george
```

Or swap voices on an existing transcript:

```cmd
podgen --from-transcript .\output\transcript.md -o .\output ^
  --voice-a af_bella --voice-b bm_lewis
```

## Quality Notes

- All preset voices are **zero-shot trained**; you cannot clone your own voice with Kokoro.
- Some voices have more expressive range than others. `af_heart`, `am_michael`, `bf_emma`, and `bm_george` are the most consistent for long-form content.
- Kokoro's quality degrades on very long single generations. podgen chunks turns at ~400 chars (`@src/podgen/tts.py:14`) to mitigate this.
- If you need voice cloning, plan to add a Chatterbox or F5-TTS backend (see the roadmap in `README.md`).

## Tuning

Kokoro's `speed` parameter (in `KokoroTTS.synth`) controls playback speed (1.0 = normal). Not yet exposed via CLI in v1.0; you can modify `@src/podgen/cli.py` to pass it through if you want speaker-specific pacing.
