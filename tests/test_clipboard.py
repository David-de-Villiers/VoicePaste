from voicepaste.clipboard import copy_text


class FakeStdin:
    def __init__(self):
        self.text = ""
        self.closed = False

    def write(self, text):
        self.text += text

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self):
        self.stdin = FakeStdin()
        self.stderr = None
        self.returncode = None

    def poll(self):
        return None


def test_xclip_copy_does_not_wait_for_clipboard_owner(monkeypatch):
    fake = FakeProcess()
    calls = []
    monkeypatch.setattr("voicepaste.clipboard.available_clipboard_tools", lambda session_type=None: ["xclip"])
    monkeypatch.setattr("voicepaste.clipboard.time.sleep", lambda seconds: None)

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return fake

    monkeypatch.setattr("voicepaste.clipboard.subprocess.Popen", fake_popen)
    ok, message = copy_text("hello", "x11")
    assert ok is True
    assert message == "copied with xclip"
    assert fake.stdin.text == "hello"
    assert fake.stdin.closed is True
    assert calls[0][1]["start_new_session"] is True
