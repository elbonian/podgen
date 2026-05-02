"""CLI entry point."""
from __future__ import annotations

import json
from pathlib import Path

from .platform_paths import ensure_tools_on_path

ensure_tools_on_path()

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .assemble import stitch
from .ingest import combine_docs, load_folder
from .llm import build_client
from .transcript import generate_transcript, parse_transcript

app = typer.Typer(add_completion=False, help="Local NotebookLM-style podcast generator.")
console = Console()


@app.command()
def generate(
    source_dir: Path = typer.Option(None, "--source-dir", "-s", exists=True, file_okay=False, help="Folder of documents (omit if using --from-transcript)."),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", "-o", help="Where to write transcript + audio."),
    guidance: str = typer.Option("", "--guidance", "-g", help="Focus/tone guidance for the podcast."),
    duration: int = typer.Option(5, "--duration", "-d", min=1, max=60, help="Target duration in minutes."),
    speaker_a: str = typer.Option("Alex", "--speaker-a", help="Name for speaker A."),
    speaker_b: str = typer.Option("Jordan", "--speaker-b", help="Name for speaker B."),
    voice_a: str = typer.Option("af_heart", "--voice-a", help="Kokoro voice id for speaker A."),
    voice_b: str = typer.Option("am_michael", "--voice-b", help="Kokoro voice id for speaker B."),
    backend: str = typer.Option("anthropic", "--backend", help="LLM backend: 'anthropic' or 'lmstudio'."),
    model: str = typer.Option("claude-sonnet-4-5", "--model", help="Model id (Anthropic) or LM Studio model name."),
    base_url: str = typer.Option(None, "--base-url", help="Override for OpenAI-compatible endpoint (default: http://localhost:1234/v1)."),
    audio_format: str = typer.Option("mp3", "--format", help="mp3 or wav."),
    transcript_only: bool = typer.Option(False, "--transcript-only", help="Skip TTS; just write transcript."),
    from_transcript: Path = typer.Option(None, "--from-transcript", help="Skip LLM; synthesize audio from an existing transcript.md/.json."),
) -> None:
    """Generate a podcast from a folder of documents."""
    load_dotenv()
    output_dir.mkdir(parents=True, exist_ok=True)

    if from_transcript is not None:
        raw = from_transcript.read_text(encoding="utf-8")
        console.print(f"[green]Loaded transcript from:[/green] {from_transcript}")
    else:
        if source_dir is None:
            console.print("[red]Error: --source-dir is required (or use --from-transcript).[/red]")
            console.print("Run [bold]podgen --help[/bold] for usage.")
            raise typer.Exit(1)
        # 1. Ingest
        with console.status("[bold cyan]Reading documents..."):
            docs = load_folder(source_dir)
        if not docs:
            console.print("[red]No supported documents found (.txt, .md, .pdf).[/red]")
            raise typer.Exit(1)
        console.print(f"[green]Loaded {len(docs)} document(s).[/green]")
        combined = combine_docs(docs)

        # 2. Transcript
        llm = build_client(backend=backend, model=model, base_url=base_url)
        with console.status(f"[bold cyan]Generating transcript via {backend}:{model}..."):
            raw = generate_transcript(
                client=llm,
                source_text=combined,
                guidance=guidance,
                duration_min=duration,
                speaker_a=speaker_a,
                speaker_b=speaker_b,
            )
        transcript_path = output_dir / "transcript.md"
        transcript_path.write_text(raw, encoding="utf-8")
        console.print(f"[green]Transcript written:[/green] {transcript_path}")

    turns = parse_transcript(raw)
    if not turns:
        console.print("[red]Failed to parse any SPEAKER_A/SPEAKER_B turns from transcript.[/red]")
        raise typer.Exit(2)
    console.print(f"[green]Parsed {len(turns)} turns.[/green]")

    (output_dir / "transcript.json").write_text(
        json.dumps([{"speaker": t.speaker, "text": t.text} for t in turns], indent=2),
        encoding="utf-8",
    )

    if transcript_only:
        return

    # 3. TTS
    from .tts import KokoroTTS  # lazy import (heavy)

    console.print("[bold cyan]Loading Kokoro TTS...[/bold cyan]")
    tts = KokoroTTS()

    segments = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Synthesizing turns", total=len(turns))
        for turn in turns:
            voice = voice_a if turn.speaker == "A" else voice_b
            audio = tts.synth(turn.text, voice=voice)
            segments.append(audio)
            progress.advance(task)

    # 4. Stitch
    out_ext = "mp3" if audio_format.lower() == "mp3" else "wav"
    audio_path = output_dir / f"podcast.{out_ext}"
    with console.status(f"[bold cyan]Stitching to {audio_path.name}..."):
        stitch(segments, audio_path)
    console.print(f"[bold green]Done:[/bold green] {audio_path}")


if __name__ == "__main__":
    app()
