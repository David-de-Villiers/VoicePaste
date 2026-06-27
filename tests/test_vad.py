import numpy as np

from voicepaste.vad import SilenceDetector, estimate_threshold, frame_rms


def test_frame_rms_for_synthetic_audio():
    samples = np.array([0.0, 1.0, -1.0, 0.0], dtype=np.float32)
    assert round(frame_rms(samples), 3) == 0.707


def test_silence_detector_stops_after_sustained_silence():
    detector = SilenceDetector(sample_rate=10, threshold=0.1, silence_seconds=0.3, min_seconds=0.1, max_seconds=5)
    assert detector.update(np.ones(2, dtype=np.float32) * 0.5) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) == "silence"


def test_silence_detector_max_duration_stop():
    detector = SilenceDetector(sample_rate=10, threshold=0.1, silence_seconds=5, min_seconds=0.1, max_seconds=0.3)
    assert detector.update(np.ones(2, dtype=np.float32) * 0.5) is None
    assert detector.update(np.ones(2, dtype=np.float32) * 0.5) == "max-seconds"


def test_min_duration_prevents_immediate_cutoff():
    detector = SilenceDetector(sample_rate=10, threshold=0.1, silence_seconds=0.1, min_seconds=0.5, max_seconds=5)
    assert detector.update(np.ones(1, dtype=np.float32) * 0.5) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) == "silence"


def test_silence_detector_stops_without_prior_speech_after_min_duration():
    detector = SilenceDetector(sample_rate=10, threshold=0.1, silence_seconds=0.3, min_seconds=0.5, max_seconds=5)
    assert detector.update(np.zeros(2, dtype=np.float32)) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) is None
    assert detector.update(np.zeros(2, dtype=np.float32)) == "silence"


def test_estimate_threshold_has_floor_and_scales_noise():
    assert estimate_threshold(0.0) == 0.005
    assert estimate_threshold(0.01) == 0.03
