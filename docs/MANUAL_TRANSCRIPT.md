# Generating a Transcript Manually (Claude / ChatGPT / any chat UI)

You can skip the `podgen` LLM integration entirely and generate the transcript
yourself using any chat interface (Claude.ai, ChatGPT, Gemini, Mistral Chat,
local LM Studio chat tab, etc.), then use `--from-transcript` to synthesize
audio. Useful when:

- You want to edit the transcript by hand before TTS.
- You want to use a model that `podgen` doesn't directly support.
- You don't want to install/configure API keys or local servers.
- You already have a transcript written and just want audio.

## The Prompt Files

podgen's prompts live as plain Markdown so you can copy them directly:

- **System prompt**: [`src/podgen/prompts/transcript_system.md`](../src/podgen/prompts/transcript_system.md)
- **User prompt template**: [`src/podgen/prompts/transcript_user.md`](../src/podgen/prompts/transcript_user.md)

These are the single source of truth — `podgen` loads them at runtime via
`importlib.resources`. If you modify them, the CLI picks up the change on the
next run.

## Manual Workflow

### Step 1 — Set up the system prompt

In Claude.ai or ChatGPT, put the contents of
[`transcript_system.md`](../src/podgen/prompts/transcript_system.md) as the
**system prompt** or a Custom Instruction / Project instruction. In a plain
chat UI without a system field, paste it as your first message prefixed with
"Follow these rules for all following messages:".

### Step 2 — Fill in the user prompt template

Copy [`transcript_user.md`](../src/podgen/prompts/transcript_user.md) and
replace the `{placeholder}` fields:

| Placeholder | Replace with |
|---|---|
| `{speaker_a}` | Speaker A's name, e.g. `Alex` |
| `{speaker_b}` | Speaker B's name, e.g. `Jordan` |
| `{target_words}` | Target word count = `duration_minutes × 150` |
| `{duration_min}` | Target duration in minutes |
| `{words_per_minute}` | `150` |
| `{guidance}` | Your focus/tone prompt, or `(none - use your judgment)` |
| `{source_text}` | Your source material (paste documents here) |

Submit this as a user message.

### Step 3 — Save the output

The model should respond with lines like:

```
SPEAKER_A: Welcome to the show...
SPEAKER_B: Thanks for having me...
SPEAKER_A: Let's dive in...
```

Save this to a file, e.g. `my_transcript.md`.

### Step 4 — Synthesize audio with podgen

```cmd
podgen --from-transcript .\my_transcript.md -o .\output
```

That's it. podgen parses the `SPEAKER_A:` / `SPEAKER_B:` prefixes and
synthesizes each turn with Kokoro.

## Example — 5-minute technical podcast

1. Compute `target_words = 5 * 150 = 750`.
2. Paste the system prompt into Claude.
3. Fill in the user template:

   ```
   Generate a two-speaker podcast transcript from the source material below.

   SPEAKER_A is named "Alex". SPEAKER_B is named "Jordan". They do NOT need
   to say their names repeatedly; just converse naturally.

   Target length: approximately 750 words (~5 minutes of spoken audio at
   150 wpm).

   User guidance / focus:
   Focus on the core architectural decisions. SPEAKER_A is curious,
   SPEAKER_B is the subject-matter expert.

   Source material:
   [paste your document text here]

   Now write the full transcript. Remember: every line must start with
   "SPEAKER_A:" or "SPEAKER_B:".
   ```

4. Save Claude's response to `transcript.md`.
5. Run:

   ```cmd
   podgen --from-transcript .\transcript.md -o .\output
   ```

## Tips

- **Editing before TTS**: open the transcript file, fix anything that reads
  awkwardly or that the model got wrong, then run TTS. This gives you full
  editorial control.
- **Longer generations**: for podcasts beyond ~10 minutes, some models produce
  shallow dialogue. Split into sections, generate each, concatenate, then run
  TTS on the combined file.
- **Hand-writing from scratch**: you don't need a model at all. A plain
  `.md` file with `SPEAKER_A:` / `SPEAKER_B:` prefixed lines is all
  `--from-transcript` needs.
- **Proper nouns**: Kokoro sometimes mispronounces rare words. After
  generating the transcript, do a search-and-replace with phonetic spelling
  (e.g. "F Prime" → "Eff Prime") before running TTS.
