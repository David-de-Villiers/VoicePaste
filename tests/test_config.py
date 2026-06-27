from pathlib import Path

from voicepaste.config import Config, load_config, write_default_config


def test_default_config_values():
    cfg = Config()
    assert cfg.backend == "faster-whisper"
    assert cfg.model_tier == "cpu"
    assert cfg.model_id_for_tier("accuracy") == "Systran/faster-whisper-large-v3-turbo"


def test_load_partial_config_merges_defaults(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text('model_tier = "fast"\n[insertion]\npaste_key = "ctrl+shift+v"\n')
    cfg = load_config(path)
    assert cfg.model_tier == "fast"
    assert cfg.insertion.paste_key == "ctrl+shift+v"
    assert cfg.models.cpu == "Systran/faster-whisper-small.en"


def test_write_default_config_is_non_destructive(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text('model_tier = "accuracy"\n')
    write_default_config(path)
    assert path.read_text() == 'model_tier = "accuracy"\n'
