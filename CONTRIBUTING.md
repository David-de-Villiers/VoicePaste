# Contributing

Thanks for considering a contribution to VoicePaste.

## Development Setup

```bash
/usr/bin/python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

## Checks

Run these before opening a pull request:

```bash
python -m compileall src tests
pytest -q
```

Optional linting:

```bash
ruff check .
```

## Scope

VoicePaste is intentionally local/offline and terminal-first. Please do not add cloud transcription, telemetry, a GUI, a tray application, a daemon, or a global hotkey listener without prior discussion.

Hardware-dependent changes should keep tests mocked or optional so CI does not require a microphone, GPU, display server, downloaded model, or desktop insertion tools.
