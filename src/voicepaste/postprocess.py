from __future__ import annotations

import re


def cleanup_text(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()
