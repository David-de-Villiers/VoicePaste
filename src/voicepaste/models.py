from __future__ import annotations

"""Local model path and download helpers."""

from pathlib import Path
import re

from .config import Config, model_dir


def model_local_path(model_id: str, base_dir: Path | None = None) -> Path:
    """Map a model identifier to its local cache path."""

    safe = re.sub(r"[^A-Za-z0-9_.-]+", "--", model_id).strip("-")
    return (base_dir or model_dir()) / safe


def fetch_model(cfg: Config, tier: str) -> Path:
    """Download a configured model tier for offline use."""

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("huggingface-hub is not installed") from exc
    model_id = cfg.model_id_for_tier(tier)
    target = model_local_path(model_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=model_id, local_dir=target, local_dir_use_symlinks=False)
    return target


def require_local_model(cfg: Config, tier: str | None = None) -> Path:
    """Return a local model path or raise with setup guidance."""

    model_id = cfg.model_id_for_tier(tier)
    path = model_local_path(model_id)
    if not path.exists():
        raise RuntimeError(f"local model not found at {path}; run `voicepaste models fetch --tier {tier or cfg.model_tier}`")
    return path
