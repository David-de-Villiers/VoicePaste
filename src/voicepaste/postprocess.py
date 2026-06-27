from __future__ import annotations

import re

from .config import Config, GlossaryConfig


def cleanup_text(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def apply_glossary(text: str, glossary: GlossaryConfig) -> str:
    if not glossary.enabled or not glossary.replacements:
        return text
    result = text
    for source, replacement in sorted(glossary.replacements.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(rf"(?<!\w){re.escape(source)}(?!\w)", re.IGNORECASE)
        result = pattern.sub(replacement, result)
    return result


def final_transcript(raw_text: str, cfg: Config) -> str:
    return apply_glossary(cleanup_text(raw_text), cfg.glossary)
