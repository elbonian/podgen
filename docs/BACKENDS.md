# LLM Backends

podgen supports two code paths but many providers. All dispatch happens in `@src/podgen/llm.py` via `build_client`.

## Backend Comparison

| Backend | Class | Best For | Cost | Setup |
|---|---|---|---|---|
| Anthropic | `AnthropicClient` | Highest-quality transcripts | ~$0.05–0.30 / podcast | API key |
| LM Studio | `OpenAICompatibleClient` | Fully local, zero cost | $0 | Local server |
| Ollama | `OpenAICompatibleClient` | Fully local, CLI-driven | $0 | `--base-url` |
| vLLM | `OpenAICompatibleClient` | High-throughput local | $0 | `--base-url` |
| llama.cpp server | `OpenAICompatibleClient` | Minimal, CPU-friendly | $0 | `--base-url` |
| OpenAI | `OpenAICompatibleClient` | If you already have a key | ~$0.01–0.10 / podcast | API key + `--base-url` |

## Anthropic

```cmd
podgen -s .\docs --backend anthropic --model claude-sonnet-4-5
```

- **Requires**: `ANTHROPIC_API_KEY` in `.env` or environment.
- **Model suggestions**:
  - `claude-sonnet-4-5` — balanced quality/cost (default).
  - `claude-opus-4-1` — highest quality for nuanced material.
  - `claude-haiku-4-5` — fast and cheap for short podcasts.
- **Advantages**: best dialogue naturalness, reliable instruction following, long context (200k tokens) means no need to truncate most corpora.

## LM Studio

```cmd
podgen -s .\docs --backend lmstudio --model "openai/gpt-oss-20b"
```

- **Requires**: LM Studio running with a model loaded and the local server started (port 1234 by default).
- **Default endpoint**: `http://localhost:1234/v1`.
- **Check available models**:
  ```cmd
  curl http://localhost:1234/v1/models
  ```
- **Recommended models** (in order of quality for long-form dialogue):
  - **Qwen 2.5 72B Instruct** — excellent dialogue, needs 48 GB+ VRAM
  - **Llama 3.3 70B Instruct** — strong general model
  - **Qwen 2.5 32B Instruct** — great balance, ~24 GB VRAM
  - **Mistral Small 24B** — fast, solid quality
  - **gpt-oss-20b** — what we tested with, good for short/medium podcasts
- **Gotcha**: set the model's context length ≥ 32k in LM Studio before loading. The default is often too small for ingested documents. See `@docs/TROUBLESHOOTING.md`.

## Ollama

```cmd
podgen -s .\docs --backend lmstudio --base-url http://localhost:11434/v1 ^
  --model "llama3.3:70b"
```

- **Note**: `--backend lmstudio` is just the OpenAI-compatible alias; it works with any compliant server.
- **Endpoint**: Ollama exposes `/v1` on port 11434 by default.

## vLLM

```cmd
podgen -s .\docs --backend lmstudio --base-url http://localhost:8000/v1 ^
  --model "meta-llama/Meta-Llama-3.1-70B-Instruct"
```

Use this when you want max tokens/sec. Launch vLLM with:

```bash
vllm serve meta-llama/Meta-Llama-3.1-70B-Instruct --port 8000
```

## llama.cpp server

```cmd
podgen -s .\docs --backend lmstudio --base-url http://localhost:8080/v1 ^
  --model "whatever-you-loaded"
```

Start with:

```bash
llama-server -m path/to/model.gguf --port 8080 -c 32768
```

The `-c` flag sets context length — make sure it's big enough (see Troubleshooting).

## OpenAI (Cloud)

```cmd
set OPENAI_API_KEY=sk-...
podgen -s .\docs --backend lmstudio --base-url https://api.openai.com/v1 ^
  --model "gpt-4o"
```

Yes, the `lmstudio` backend name is misleading here — it's really "OpenAI-compatible". You can also set `OPENAI_BASE_URL` env var instead of `--base-url`.

## Adding a New Backend

To add a backend with its own SDK (e.g. Google Gemini, Mistral direct):

1. Add a class to `@src/podgen/llm.py`:

   ```python
   class GeminiClient:
       def __init__(self, model: str):
           from google.generativeai import GenerativeModel
           self.client = GenerativeModel(model)

       def complete(self, system: str, user: str, max_tokens: int) -> str:
           resp = self.client.generate_content(
               [system, user],
               generation_config={"max_output_tokens": max_tokens},
           )
           return resp.text.strip()
   ```

2. Add a branch to `build_client`:

   ```python
   if backend == "gemini":
       return GeminiClient(model=model)
   ```

3. Add the SDK to `pyproject.toml` dependencies.
4. Document it here and in `README.md`.

## Advanced: Environment Variables

The OpenAI-compatible client respects:

- `OPENAI_API_KEY` — sent as bearer token (local servers ignore it but still require *something*; podgen defaults to `"not-needed"`).
- `OPENAI_BASE_URL` — overrides `--base-url` if set.

These come from the `openai` SDK itself.

## Cost Estimation

Rough per-podcast costs at 5-minute duration (~750 input words, ~5000 output tokens):

| Provider / Model | Input cost | Output cost | Total |
|---|---|---|---|
| Claude Sonnet 4.5 | $0.003 | $0.075 | ~$0.08 |
| Claude Opus 4.1 | $0.015 | $0.375 | ~$0.39 |
| Claude Haiku 4.5 | $0.0008 | $0.020 | ~$0.02 |
| OpenAI GPT-4o | $0.002 | $0.050 | ~$0.05 |
| Any local | — | — | **$0.00** |

For the TTS stage, Kokoro is local and free regardless of backend choice.
