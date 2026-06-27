from voicepaste.cli import RuntimeOptions, _handle_transcript


def test_copy_only_avoids_paste(monkeypatch, capsys):
    paste_calls = []
    copy_calls = []
    monkeypatch.setattr("voicepaste.cli.save_last_transcript", lambda text: None)
    monkeypatch.setattr("voicepaste.cli.insert_or_copy", lambda text, cfg: paste_calls.append(text))
    monkeypatch.setattr("voicepaste.clipboard.copy_text", lambda text, session_type=None: copy_calls.append(text) or (True, "copied"))
    monkeypatch.setattr("voicepaste.insert.session_type", lambda: "x11")

    assert _handle_transcript(" hello   world ", RuntimeOptions(paste=False)) == 0

    assert paste_calls == []
    assert copy_calls == ["hello world"]
    assert capsys.readouterr().out == "hello world\n"


def test_no_paste_avoids_paste(monkeypatch):
    paste_calls = []
    copy_calls = []
    monkeypatch.setattr("voicepaste.cli.save_last_transcript", lambda text: None)
    monkeypatch.setattr("voicepaste.cli.insert_or_copy", lambda text, cfg: paste_calls.append(text))
    monkeypatch.setattr("voicepaste.clipboard.copy_text", lambda text, session_type=None: copy_calls.append(text) or (True, "copied"))
    monkeypatch.setattr("voicepaste.insert.session_type", lambda: "x11")

    assert _handle_transcript("hello", RuntimeOptions(paste=False)) == 0

    assert paste_calls == []
    assert copy_calls == ["hello"]
