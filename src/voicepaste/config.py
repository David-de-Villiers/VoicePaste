from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib


APP_NAME = "voicepaste"


def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME / "config.toml"


def data_dir() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME


def state_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / APP_NAME


def model_dir() -> Path:
    return data_dir() / "models"


@dataclass(frozen=True)
class InsertionConfig:
    prefer_clipboard_paste: bool = True
    restore_clipboard: bool = False
    paste_key: str = "ctrl+v"


@dataclass(frozen=True)
class ModelConfig:
    fast: str = "Systran/faster-whisper-small.en"
    small: str = "Systran/faster-whisper-small.en"
    cpu: str = "Systran/faster-whisper-small.en"
    accuracy: str = "Systran/faster-whisper-large-v3-turbo"


@dataclass(frozen=True)
class GlossaryConfig:
    enabled: bool = True
    replacements: dict[str, str] = field(
        default_factory=lambda: {
            "de-separation": "d-separation",
            "D separation": "d-separation",
            "d separation": "d-separation",
            "latex": "LaTeX",
            "bayesian network": "Bayesian network",
            "bayesian networks": "Bayesian networks",
        }
    )


@dataclass(frozen=True)
class Config:
    backend: str = "faster-whisper"
    model_tier: str = "cpu"
    language: str = "en"
    record_sample_rate: int = 16000
    max_record_seconds: int = 120
    delete_audio: bool = True
    initial_prompt: str = (
        "Bayesian networks, conditional independence, d-separation, expected utility, "
        "LaTeX, probabilistic graphical models, posterior, prior, likelihood, inference."
    )
    insertion: InsertionConfig = field(default_factory=InsertionConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    glossary: GlossaryConfig = field(default_factory=GlossaryConfig)

    def normalize_model_tier(self, tier: str | None = None) -> str:
        selected = tier or self.model_tier
        if selected == "cpu":
            return "cpu"
        if selected not in {"fast", "small", "accuracy"}:
            raise ValueError(f"unknown model tier: {selected}")
        return selected

    def model_id_for_tier(self, tier: str | None = None) -> str:
        selected = self.normalize_model_tier(tier)
        return getattr(self.models, selected)


def _merge_table(defaults: dict, overrides: dict) -> dict:
    merged = defaults.copy()
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_table(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_config_dict() -> dict:
    return {
        "backend": "faster-whisper",
        "model_tier": "cpu",
        "language": "en",
        "record_sample_rate": 16000,
        "max_record_seconds": 120,
        "delete_audio": True,
        "initial_prompt": (
            "Bayesian networks, conditional independence, d-separation, expected utility, "
            "LaTeX, probabilistic graphical models, posterior, prior, likelihood, inference."
        ),
        "insertion": {
            "prefer_clipboard_paste": True,
            "restore_clipboard": False,
            "paste_key": "ctrl+v",
        },
        "models": {
            "fast": "Systran/faster-whisper-small.en",
            "small": "Systran/faster-whisper-small.en",
            "cpu": "Systran/faster-whisper-small.en",
            "accuracy": "Systran/faster-whisper-large-v3-turbo",
        },
        "glossary": {
            "enabled": True,
            "replacements": {
                "de-separation": "d-separation",
                "D separation": "d-separation",
                "d separation": "d-separation",
                "latex": "LaTeX",
                "bayesian network": "Bayesian network",
                "bayesian networks": "Bayesian networks",
            },
        },
    }


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    raw = default_config_dict()
    if path.exists():
        with path.open("rb") as fh:
            raw = _merge_table(raw, tomllib.load(fh))
    return Config(
        backend=str(raw["backend"]),
        model_tier=str(raw["model_tier"]),
        language=str(raw["language"]),
        record_sample_rate=int(raw["record_sample_rate"]),
        max_record_seconds=int(raw["max_record_seconds"]),
        delete_audio=bool(raw["delete_audio"]),
        initial_prompt=str(raw.get("initial_prompt", "")),
        insertion=InsertionConfig(**raw["insertion"]),
        models=ModelConfig(**raw["models"]),
        glossary=GlossaryConfig(**raw["glossary"]),
    )


def write_default_config(path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            '\n'.join(
                [
                    'backend = "faster-whisper"',
                    'model_tier = "cpu"',
                    'language = "en"',
                    'record_sample_rate = 16000',
                    'max_record_seconds = 120',
                    'delete_audio = true',
                    'initial_prompt = "Bayesian networks, conditional independence, d-separation, expected utility, LaTeX, probabilistic graphical models, posterior, prior, likelihood, inference."',
                    "",
                    "[insertion]",
                    "prefer_clipboard_paste = true",
                    "restore_clipboard = false",
                    'paste_key = "ctrl+v"',
                    "",
                    "[models]",
                    'fast = "Systran/faster-whisper-small.en"',
                    'small = "Systran/faster-whisper-small.en"',
                    'cpu = "Systran/faster-whisper-small.en"',
                    'accuracy = "Systran/faster-whisper-large-v3-turbo"',
                    "",
                    "[glossary]",
                    "enabled = true",
                    "",
                    "[glossary.replacements]",
                    '"de-separation" = "d-separation"',
                    '"D separation" = "d-separation"',
                    '"d separation" = "d-separation"',
                    'latex = "LaTeX"',
                    '"bayesian network" = "Bayesian network"',
                    '"bayesian networks" = "Bayesian networks"',
                    "",
                ]
            )
        )
    return path
