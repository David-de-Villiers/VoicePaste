from __future__ import annotations

"""Small state helpers for the last transcript."""

from pathlib import Path

from .config import state_dir


def last_transcript_path() -> Path:
    """Return the XDG state path for the last transcript."""

    return state_dir() / "last.txt"


def save_last_transcript(text: str, path: Path | None = None) -> Path:
    """Persist the last final transcript locally."""

    target = path or last_transcript_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def read_last_transcript(path: Path | None = None) -> str | None:
    """Read the last transcript if one exists."""

    target = path or last_transcript_path()
    if not target.exists():
        return None
    return target.read_text(encoding="utf-8")
