"""Document ingestion. MVP: .txt, .md, .pdf."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

SUPPORTED = {".txt", ".md", ".pdf"}


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_folder(folder: Path) -> list[tuple[str, str]]:
    """Return list of (filename, text) for supported files in folder (recursive)."""
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Source folder not found: {folder}")

    docs: list[tuple[str, str]] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        try:
            text = _read_pdf(path) if path.suffix.lower() == ".pdf" else _read_text(path)
        except Exception as e:
            print(f"[warn] skipping {path.name}: {e}")
            continue
        text = text.strip()
        if text:
            docs.append((str(path.relative_to(folder)), text))
    return docs


def combine_docs(docs: list[tuple[str, str]], max_chars: int = 120_000) -> str:
    """Concatenate docs with headers. Truncate naively if over budget (MVP)."""
    blocks = [f"===== {name} =====\n{text}" for name, text in docs]
    combined = "\n\n".join(blocks)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[...truncated for context budget...]"
    return combined
