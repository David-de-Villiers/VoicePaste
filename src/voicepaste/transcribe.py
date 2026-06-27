from __future__ import annotations

"""Local faster-whisper transcription backend."""

from dataclasses import dataclass
from pathlib import Path
import time

from .config import Config
from .models import require_local_model


@dataclass(frozen=True)
class TranscriptionResult:
    """Result metadata for one local transcription run."""

    text: str
    duration_seconds: float
    backend: str
    model_path: Path
    device: str
    compute_type: str


def _cuda_available() -> bool:
    try:
        import ctranslate2

        return bool(ctranslate2.get_supported_compute_types("cuda"))
    except Exception:
        return False


def select_device_and_compute(device: str = "auto", prefer_gpu: bool = True) -> tuple[str, str]:
    """Choose the CTranslate2 device and compute type for ASR."""

    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError(f"unsupported device: {device}")
    if device == "cpu":
        return "cpu", "int8"
    if device == "cuda":
        if not _cuda_available():
            raise RuntimeError("CUDA requested but CTranslate2 cannot use CUDA")
        return "cuda", "float16"
    if prefer_gpu and _cuda_available():
        return "cuda", "float16"
    return "cpu", "int8"


def transcribe_file(
    path: Path,
    cfg: Config,
    tier: str | None = None,
    prefer_gpu: bool = True,
    device: str = "auto",
    language: str | None = None,
    initial_prompt: str | None = None,
) -> TranscriptionResult:
    """Transcribe a local audio file with a locally cached faster-whisper model.

    Args:
        path: Local audio file to transcribe.
        cfg: Loaded VoicePaste configuration.
        tier: Optional model tier override.
        prefer_gpu: Whether `auto` may choose CUDA.
        device: `auto`, `cpu`, or `cuda`.
        language: Optional language override.
        initial_prompt: Optional faster-whisper prompt override. If omitted,
            the configured prompt is used.

    Returns:
        TranscriptionResult containing text and backend metadata.
    """

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed") from exc
    model_path = require_local_model(cfg, tier)
    selected_device, compute_type = select_device_and_compute(device, prefer_gpu)
    started = time.monotonic()
    model = WhisperModel(str(model_path), device=selected_device, compute_type=compute_type)
    prompt = cfg.initial_prompt if initial_prompt is None else initial_prompt
    segments, _info = model.transcribe(
        str(path),
        language=language or cfg.language,
        vad_filter=True,
        initial_prompt=prompt or None,
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return TranscriptionResult(
        text=text,
        duration_seconds=time.monotonic() - started,
        backend=cfg.backend,
        model_path=model_path,
        device=selected_device,
        compute_type=compute_type,
    )
