from __future__ import annotations

"""Lightweight RMS-based voice activity detection."""

from dataclasses import dataclass

import numpy as np


def silence_recording_available() -> bool:
    """Return whether shortcut silence recording is implemented."""

    return True


def frame_rms(samples: np.ndarray) -> float:
    """Compute root mean square amplitude for audio samples."""

    if samples.size == 0:
        return 0.0
    data = samples.astype(np.float32, copy=False)
    return float(np.sqrt(np.mean(data * data)))


@dataclass
class SilenceDetector:
    """Stateful RMS silence detector for streaming audio frames."""

    sample_rate: int
    threshold: float
    silence_seconds: float
    min_seconds: float
    max_seconds: float
    elapsed_seconds: float = 0.0
    silent_seconds: float = 0.0
    speech_seen: bool = False

    def update(self, frame: np.ndarray) -> str | None:
        """Update detector state and return a stop reason when triggered."""

        frame_seconds = len(frame) / float(self.sample_rate)
        self.elapsed_seconds += frame_seconds
        rms = frame_rms(frame)
        if rms >= self.threshold:
            self.speech_seen = True
            self.silent_seconds = 0.0
        else:
            self.silent_seconds += frame_seconds

        if self.elapsed_seconds >= self.max_seconds:
            return "max-seconds"
        if self.elapsed_seconds < self.min_seconds:
            return None
        if self.silent_seconds >= self.silence_seconds:
            return "silence"
        return None


def estimate_threshold(noise_rms: float) -> float:
    """Estimate a conservative VAD threshold from ambient room RMS."""

    return max(0.005, min(0.08, noise_rms * 3.0))
