from __future__ import annotations

"""Audio capture and WAV inspection helpers.

This module owns microphone interaction and temporary WAV creation. It avoids
ASR, clipboard, and desktop concerns so recording can be tested and reused by
commands such as `record-test`, `quality-test`, and shortcut mode.
"""

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
import tempfile
import time
import wave

import numpy as np

from .vad import SilenceDetector, estimate_threshold, frame_rms


@dataclass(frozen=True)
class AudioStats:
    """Summary statistics for a local WAV recording."""

    path: Path
    duration_seconds: float
    rms: float
    sample_rate: int


@dataclass(frozen=True)
class RecordingResult:
    """Result of an automatic recording session."""

    path: Path
    reason: str
    duration_seconds: float


def _import_sounddevice():
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("sounddevice is not installed; run `python -m pip install -e '.[dev]'`") from exc
    return sd


def record_until_enter(sample_rate: int, max_seconds: int) -> Path:
    """Record from the default input until the user presses Enter."""

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
    """Record a fixed-duration mono WAV from the default input."""

    sd = _import_sounddevice()
    frames = int(seconds * sample_rate)
    print(f"Recording {seconds:.1f}s from default input...")
    data = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return write_wav(data.reshape(-1), sample_rate)


def record_immediate(
    sample_rate: int,
    *,
    stop_on_silence: bool,
    silence_seconds: float,
    max_seconds: float,
    min_seconds: float,
    vad_threshold: float,
    block_seconds: float = 0.1,
) -> RecordingResult:
    """Record immediately and stop on silence or maximum duration.

    Args:
        sample_rate: Capture sample rate in Hz.
        stop_on_silence: Whether RMS-based silence should stop recording.
        silence_seconds: Sustained silence duration required to stop.
        max_seconds: Hard recording limit.
        min_seconds: Minimum duration before silence can stop recording.
        vad_threshold: RMS threshold below which a frame is considered silent.
        block_seconds: Input stream callback block duration.

    Returns:
        RecordingResult containing the temporary WAV path and stop reason.
    """

    sd = _import_sounddevice()
    queue: Queue[np.ndarray] = Queue()
    blocksize = max(1, int(sample_rate * block_seconds))
    detector = SilenceDetector(
        sample_rate=sample_rate,
        threshold=vad_threshold,
        silence_seconds=silence_seconds,
        min_seconds=min_seconds,
        max_seconds=max_seconds,
    )
    chunks: list[np.ndarray] = []
    reason = "max-seconds"
    started = time.monotonic()

    def callback(indata, frames, time_info, status):  # noqa: ANN001
        queue.put(indata.copy().reshape(-1))

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", blocksize=blocksize, callback=callback):
        while True:
            try:
                frame = queue.get(timeout=0.25)
            except Empty:
                if time.monotonic() - started >= max_seconds:
                    reason = "max-seconds"
                    break
                continue
            chunks.append(frame)
            if stop_on_silence:
                stop_reason = detector.update(frame)
            else:
                detector.elapsed_seconds += len(frame) / float(sample_rate)
                stop_reason = "max-seconds" if detector.elapsed_seconds >= max_seconds else None
            if stop_reason:
                reason = stop_reason
                break

    if not chunks:
        raise RuntimeError("no audio captured")
    captured = np.concatenate(chunks).reshape(-1)
    path = write_wav(captured, sample_rate)
    return RecordingResult(path=path, reason=reason, duration_seconds=len(captured) / float(sample_rate))


def calibrate_noise(seconds: float, sample_rate: int) -> tuple[float, float, Path]:
    """Record ambient noise and estimate a VAD threshold.

    Returns:
        A tuple of `(ambient_rms, suggested_threshold, wav_path)`.
    """

    path = record_fixed(seconds, sample_rate)
    with wave.open(str(path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    rms = frame_rms(samples)
    return rms, estimate_threshold(rms), path


def write_wav(audio: np.ndarray, sample_rate: int) -> Path:
    """Write mono float audio samples to a temporary 16-bit WAV file."""

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
    """Read a WAV file and compute duration, sample rate, and RMS."""

    with wave.open(str(path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        sample_rate = wf.getframerate()
        duration = wf.getnframes() / float(sample_rate)
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
    return AudioStats(path=path, duration_seconds=duration, rms=rms, sample_rate=sample_rate)


def validate_audio(path: Path, min_duration: float = 0.2, min_rms: float = 0.0001) -> AudioStats:
    """Validate that a WAV file is long enough and not unexpectedly silent."""

    stats = inspect_wav(path)
    if stats.duration_seconds < min_duration:
        raise RuntimeError(f"recording is too short: {stats.duration_seconds:.2f}s")
    if stats.rms < min_rms:
        raise RuntimeError(f"recording looks silent: rms={stats.rms:.6f}")
    return stats
