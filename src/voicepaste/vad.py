from __future__ import annotations


def silence_recording_available() -> bool:
    """Placeholder for future VAD support.

    The MVP uses explicit press-to-start/press-to-stop recording because it is
    predictable across PipeWire/ALSA setups.
    """

    return False
