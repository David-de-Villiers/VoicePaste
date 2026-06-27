from __future__ import annotations

from pathlib import Path

from .config import state_dir


def last_transcript_path() -> Path:
    return state_dir() / "last.txt"


def save_last_transcript(text: str, path: Path | None = None) -> Path:
    target = path or last_transcript_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def read_last_transcript(path: Path | None = None) -> str | None:
    target = path or last_transcript_path()
    if not target.exists():
        return None
    return target.read_text(encoding="utf-8")
