from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import time
import wave

import numpy as np


@dataclass(frozen=True)
class AudioStats:
    path: Path
    duration_seconds: float
    rms: float
    sample_rate: int


def _import_sounddevice():
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("sounddevice is not installed; run `python -m pip install -e '.[dev]'`") from exc
    return sd


def record_until_enter(sample_rate: int, max_seconds: int) -> Path:
    sd = _import_sounddevice()
    chunks: list[np.ndarray] = []

    def callback(indata, frames, time_info, status):  # noqa: ANN001
        chunks.append(indata.copy())

    print("Press Enter to start recording.")
    input()
    print("Recording. Press Enter to stop.")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", callback=callback):
        started = time.monotonic()
        input()
        if time.monotonic() - started > max_seconds:
            print(f"Reached maximum recording duration of {max_seconds}s.")
    if not chunks:
        raise RuntimeError("no audio captured")
    audio = np.concatenate(chunks, axis=0).reshape(-1)
    return write_wav(audio, sample_rate)


def record_fixed(seconds: float, sample_rate: int) -> Path:
    sd = _import_sounddevice()
    frames = int(seconds * sample_rate)
    print(f"Recording {seconds:.1f}s from default input...")
    data = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return write_wav(data.reshape(-1), sample_rate)


def write_wav(audio: np.ndarray, sample_rate: int) -> Path:
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)
    tmp = tempfile.NamedTemporaryFile(prefix="voicepaste-", suffix=".wav", delete=False)
    tmp.close()
    path = Path(tmp.name)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path


def inspect_wav(path: Path) -> AudioStats:
    with wave.open(str(path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        sample_rate = wf.getframerate()
        duration = wf.getnframes() / float(sample_rate)
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
    return AudioStats(path=path, duration_seconds=duration, rms=rms, sample_rate=sample_rate)


def validate_audio(path: Path, min_duration: float = 0.2, min_rms: float = 0.0001) -> AudioStats:
    stats = inspect_wav(path)
    if stats.duration_seconds < min_duration:
        raise RuntimeError(f"recording is too short: {stats.duration_seconds:.2f}s")
    if stats.rms < min_rms:
        raise RuntimeError(f"recording looks silent: rms={stats.rms:.6f}")
    return stats
