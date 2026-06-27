from pathlib import Path

from voicepaste.state import read_last_transcript, save_last_transcript


def test_last_transcript_round_trip(tmp_path: Path):
    path = tmp_path / "last.txt"
    save_last_transcript("hello world", path)
    assert read_last_transcript(path) == "hello world"


def test_missing_last_transcript_returns_none(tmp_path: Path):
    assert read_last_transcript(tmp_path / "missing.txt") is None
