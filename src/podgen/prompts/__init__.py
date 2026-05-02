"""Prompt templates shipped as Markdown files.

Loaded at runtime via importlib.resources; also human-readable on GitHub so
users can paste them into Claude/ChatGPT for manual transcript generation.
"""
from __future__ import annotations

from importlib.resources import files


def load(name: str) -> str:
    """Load a prompt template by name (without .md extension)."""
    return files(__name__).joinpath(f"{name}.md").read_text(encoding="utf-8")
