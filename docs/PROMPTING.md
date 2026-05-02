# Prompting Guide

Two knobs shape the output: the built-in system prompt (fixed in `@src/podgen/transcript.py:11-22`) and the user's `--guidance` string.

## What the System Prompt Already Handles

The system prompt locks in:

- Two-speaker alternating format with `SPEAKER_A:` / `SPEAKER_B:` prefixes.
- Conversational tone (contractions, reactions).
- No stage directions, sound effects, or bracketed non-verbal cues.
- No fabricated facts.
- Target word count from `--duration × 150 wpm`.

You don't need to restate any of this in `--guidance`.

## What `--guidance` Is For

Use it for **editorial decisions** the system prompt can't predict:

- **Audience**: "for software engineers new to aerospace", "for a general non-technical audience", "for academic peers familiar with the field".
- **Focus**: "emphasize the core architectural decisions", "focus on the historical context, not the technical details", "spend most of the time on chapter 3".
- **Tone**: "skeptical and probing", "enthusiastic and accessible", "balanced and journalistic".
- **Perspective**: "SPEAKER_A is a proponent, SPEAKER_B is a skeptic", "both are curious learners encountering this for the first time".
- **Structure**: "start with a real-world scenario, then dive into the material", "end with practical takeaways".

## Good Examples

**Technical deep-dive:**

```
--guidance "Deep technical dive for experienced software engineers.
SPEAKER_A is the curious interviewer, SPEAKER_B is the subject-matter
expert. Spend most of the time on architectural trade-offs and real
implementation details. End with practical takeaways for someone
starting a new project."
```

**Accessible explainer:**

```
--guidance "Explain to a smart high-schooler with no prior knowledge.
Use analogies. Avoid jargon; when you must use a term, define it in
plain language. SPEAKER_A is the learner, SPEAKER_B the teacher."
```

**Skeptical review:**

```
--guidance "Critical review of the claims in the source material.
SPEAKER_A summarizes the arguments, SPEAKER_B probes for weaknesses,
missing evidence, and alternative interpretations. Balanced and fair,
not hostile."
```

**Narrative / storytelling:**

```
--guidance "Narrative retelling. Open with a concrete scene from the
source. Weave facts into a story arc rather than listing them.
Conversational and evocative, not dry."
```

**Focused excerpt:**

```
--guidance "Focus only on the Meiji Restoration section. Ignore the
prehistoric and modern sections. Explore its causes, key figures,
and lasting consequences."
```

## Common Mistakes

- **Over-constraining**: "exactly 2000 words, 20 turns, each turn exactly 3 sentences". The model will either ignore this or produce stilted output. Trust the word budget, shape the content.
- **Restating system rules**: "use SPEAKER_A and SPEAKER_B format" is already enforced.
- **Asking for things TTS can't voice**: "SPEAKER_A laughs occasionally" produces `[laughs]` in the transcript, which then gets read literally. Stick to editorial guidance.
- **Ambiguous personas**: "SPEAKER_A is technical". Technical how? Prefer role + stance: "SPEAKER_A is a senior engineer, skeptical of new frameworks".

## Tuning by Backend

- **Claude** follows nuanced guidance well — you can write a paragraph.
- **Large local models (70B+)** also follow well.
- **Small local models (≤13B)** may need simpler, more direct guidance. Lead with the most important instruction.

## Iteration Workflow

1. Generate with short guidance.
2. Read `transcript.md`.
3. Note what's off (too shallow, wrong audience, missing topic, etc.).
4. Re-run with refined guidance. The LLM call is typically the fastest part — iterate on text before running TTS.
5. Once transcript is right, run TTS (via `--from-transcript` on the saved file if you want to skip regeneration).
