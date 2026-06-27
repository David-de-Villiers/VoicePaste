from pathlib import Path

from voicepaste.cli import cmd_compare_models, cmd_quality_test
from voicepaste.transcribe import TranscriptionResult


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _result(text: str, tier: str = "cpu") -> TranscriptionResult:
    return TranscriptionResult(
        text=text,
        duration_seconds=0.5,
        backend="faster-whisper",
        model_path=Path(f"/models/{tier}"),
        device="cuda",
        compute_type="float16",
    )


def test_quality_test_prints_raw_and_final_transcript(monkeypatch, tmp_path, capsys):
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake")
    monkeypatch.setattr("voicepaste.cli.audio.validate_audio", lambda path, min_rms=0.0: type("Stats", (), {"duration_seconds": 5.0})())
    monkeypatch.setattr("voicepaste.cli.transcribe_file", lambda *args, **kwargs: _result("de-separation and latex"))

    code = cmd_quality_test(
        Args(file=str(audio_file), seconds=5, model_tier="cpu", language="en", device="cuda", keep=True)
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "raw_transcript=de-separation and latex" in out
    assert "final_transcript=d-separation and LaTeX" in out


def test_compare_models_reuses_one_audio_file(monkeypatch, tmp_path, capsys):
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake")
    record_calls = []
    transcribe_calls = []

    def fake_record(seconds, sample_rate):
        record_calls.append((seconds, sample_rate))
        return audio_file

    def fake_transcribe(path, cfg, tier=None, **kwargs):
        transcribe_calls.append((path, tier))
        return _result(f"raw {tier}", tier=tier or "none")

    monkeypatch.setattr("voicepaste.cli.audio.record_fixed", fake_record)
    monkeypatch.setattr("voicepaste.cli.audio.validate_audio", lambda path, min_rms=0.0: type("Stats", (), {"duration_seconds": 10.0})())
    monkeypatch.setattr("voicepaste.cli.transcribe_file", fake_transcribe)

    code = cmd_compare_models(
        Args(file=None, tiers="fast,cpu", seconds=10, language="en", device="cuda", keep=True)
    )

    out = capsys.readouterr().out
    assert code == 0
    assert record_calls == [(10, 16000)]
    assert transcribe_calls == [(audio_file, "fast"), (audio_file, "cpu")]
    assert "tier=fast" in out
    assert "tier=cpu" in out
