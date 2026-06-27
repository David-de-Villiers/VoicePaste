from voicepaste.config import InsertionConfig
from voicepaste.insert import InsertResult, insert_or_copy, insertion_capability


def test_insertion_capability_shape():
    cap = insertion_capability()
    assert "session" in cap
    assert "tools" in cap
    assert "can_paste" in cap
    assert "reason" in cap


def test_insert_returns_uncopied_when_clipboard_missing(monkeypatch):
    monkeypatch.setattr("voicepaste.clipboard.copy_text", lambda text, session_type=None: (False, "no clipboard"))
    result = insert_or_copy("hello", InsertionConfig())
    assert result == InsertResult(False, False, "no clipboard")


def test_insert_copied_fallback_when_paste_fails(monkeypatch):
    monkeypatch.setattr("voicepaste.clipboard.copy_text", lambda text, session_type=None: (True, "copied"))
    monkeypatch.setattr("voicepaste.insert._simulate_paste", lambda session, paste_key: (False, "paste failed"))
    result = insert_or_copy("hello", InsertionConfig())
    assert result.inserted is False
    assert result.copied is True
    assert result.message == "paste failed"
