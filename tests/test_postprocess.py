from voicepaste.config import Config, GlossaryConfig
from voicepaste.postprocess import apply_glossary, cleanup_text, final_transcript


def test_cleanup_text_trims_and_collapses_horizontal_spaces():
    assert cleanup_text("  hello   world\tagain.  ") == "hello world again."


def test_cleanup_text_preserves_punctuation():
    assert cleanup_text("  hello,   world!  ") == "hello, world!"


def test_glossary_replaces_d_separation_variants():
    glossary = GlossaryConfig(replacements={"de-separation": "d-separation", "D separation": "d-separation"})
    assert apply_glossary("This mentions de-separation.", glossary) == "This mentions d-separation."
    assert apply_glossary("This mentions D separation.", glossary) == "This mentions d-separation."


def test_glossary_handles_common_case_terms():
    cfg = Config()
    text = "latex and bayesian networks use de-separation."
    assert final_transcript(text, cfg) == "LaTeX and Bayesian networks use d-separation."
