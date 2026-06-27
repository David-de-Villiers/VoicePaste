from __future__ import annotations

"""Transcript normalization and deterministic glossary processing."""

import re

from .config import Config, GlossaryConfig


def cleanup_text(text: str) -> str:
    """Trim text and collapse accidental horizontal whitespace."""

    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def apply_glossary(text: str, glossary: GlossaryConfig) -> str:
    """Apply configured phrase replacements to a transcript."""

    if not glossary.enabled or not glossary.replacements:
        return text
    result = text
    for source, replacement in sorted(glossary.replacements.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(rf"(?<!\w){re.escape(source)}(?!\w)", re.IGNORECASE)
        result = pattern.sub(replacement, result)
    return result


def final_transcript(raw_text: str, cfg: Config) -> str:
    """Build the final transcript shown, copied, saved, and pasted."""

    return apply_glossary(cleanup_text(raw_text), cfg.glossary)
