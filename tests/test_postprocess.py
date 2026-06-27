from voicepaste.postprocess import cleanup_text


def test_cleanup_text_trims_and_collapses_horizontal_spaces():
    assert cleanup_text("  hello   world\tagain.  ") == "hello world again."


def test_cleanup_text_preserves_punctuation():
    assert cleanup_text("  hello,   world!  ") == "hello, world!"
