# VoicePaste

VoicePaste is a local/offline Linux dictation CLI. It records microphone audio, transcribes it locally with `faster-whisper`, and inserts the resulting text into the currently focused application when the desktop permits it.

VoicePaste is terminal-first and shortcut-friendly. It does not include a GUI, tray app, daemon, cloud transcription, telemetry, or remote text correction.

## Features

- Local speech-to-text after model download.
- CPU and CUDA transcription support through `faster-whisper`.
- X11 focused-window insertion using clipboard plus `xdotool`.
- Clipboard fallback with desktop notification and `paste-last`.
- GNOME custom keyboard shortcut helper without a background daemon.
- RMS-based silence stopping for shortcut-triggered dictation.
- Technical dictation glossary and faster-whisper initial prompt support.
- Diagnostics, recording test, transcription test, benchmark, quality test, and model comparison commands.

## Platform Support

Current first target:

- Ubuntu 24.04
- X11
- PipeWire/ALSA default microphone capture
- `xdotool` plus `xclip` or `xsel` for insertion
- NVIDIA CUDA when the local driver and CTranslate2 support it

Wayland support is limited. VoicePaste reports Wayland-related tool availability, but compositor restrictions can prevent focused insertion. Clipboard fallback is expected on many Wayland sessions.

## Privacy And Safety

- Audio is recorded and transcribed locally.
- Raw audio is written to temporary files and deleted by default.
- Transcripts are printed locally and stored only as the local `paste-last` state.
- No cloud ASR, LLM cleanup, telemetry, or remote logging is used by VoicePaste.
- Downloading ASR models is the setup-time network step.
- Review model licences and trust properties separately before downloading models.
- Desktop insertion depends on your Linux session and installed tools.

## Requirements

System packages for Ubuntu/X11:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev ffmpeg libportaudio2 portaudio19-dev libnotify-bin xdotool xclip xsel
```

Use a system Python virtual environment. Conda can expose an incompatible `libstdc++` to PortAudio/JACK on Ubuntu.

## Install

```bash
/usr/bin/python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
voicepaste models fetch --tier cpu
```

Run diagnostics:

```bash
voicepaste doctor
```

## Quick Start

Interactive terminal dictation:

```bash
voicepaste
```

Press Enter to start recording, press Enter again to stop, then VoicePaste transcribes and pastes.

Shortcut-friendly dictation:

```bash
voicepaste --immediate --stop-on-silence --device cuda --model-tier cpu --quiet
```

Copy without pasting:

```bash
voicepaste --copy-only
voicepaste --no-paste
```

Reuse the last transcript:

```bash
voicepaste paste-last
```

## Technical Dictation

VoicePaste uses two local, deterministic quality aids:

- `initial_prompt` is passed to faster-whisper to bias recognition toward technical terms such as Bayesian networks, conditional independence, d-separation, expected utility, and LaTeX.
- `[glossary.replacements]` runs after ASR to fix recurring terms without an LLM or network call.

Quality test:

```bash
voicepaste quality-test --seconds 10 --device cuda --model-tier small
```

Example glossary correction:

```text
raw_transcript=... de-separation and latex ...
final_transcript=... d-separation and LaTeX ...
```

Compare model tiers using one recording:

```bash
voicepaste compare-models --tiers fast,cpu --seconds 10 --device cuda
```

Model tier and device are separate:

- `--model-tier` selects the ASR model size/profile.
- `--device` selects where inference runs: `cpu`, `cuda`, or `auto`.
- `cpu` is retained as a backward-compatible tier alias for the original small CPU-safe model. Prefer `small` in new commands and configs.

For an RTX 3070 Ti Laptop GPU, start with:

```bash
voicepaste --device cuda --model-tier small
```

For higher accuracy when latency is acceptable:

```bash
voicepaste models fetch --tier accuracy
voicepaste --device cuda --model-tier accuracy
```

## GNOME Keyboard Shortcut

VoicePaste does not install a daemon or listen for global hotkeys. Bind a normal GNOME custom shortcut to a one-shot command.

Calibrate silence detection:

```bash
voicepaste calibrate-silence
```

Optionally write the suggested threshold to config:

```bash
voicepaste calibrate-silence --write
```

Print shortcut instructions:

```bash
voicepaste install-shortcut --dry-run
```

Create a helper script:

```bash
voicepaste install-shortcut --write-script
```

This writes:

```text
~/.local/bin/voicepaste-dictate
```

GNOME setup:

1. Open Settings -> Keyboard -> View and Customize Shortcuts -> Custom Shortcuts.
2. Add a shortcut named `VoicePaste Dictate`.
3. Bind it to `~/.local/bin/voicepaste-dictate` or to the full command printed by `voicepaste install-shortcut --dry-run`.

Shortcut mode starts recording immediately, shows notifications for recording/transcribing/paste/fallback/error, stops after sustained silence, and also stops at `max_seconds`. If it cuts you off too early, increase `silence_seconds` or lower `vad_threshold`. If it waits too long after you stop speaking, decrease `silence_seconds` or raise `vad_threshold`.

## Configuration

Config is stored at:

```text
~/.config/voicepaste/config.toml
```

Default shape:

```toml
backend = "faster-whisper"
model_tier = "cpu"
language = "en"
record_sample_rate = 16000
max_record_seconds = 120
delete_audio = true
initial_prompt = "Bayesian networks, conditional independence, d-separation, expected utility, LaTeX, probabilistic graphical models, posterior, prior, likelihood, inference."

[insertion]
prefer_clipboard_paste = true
restore_clipboard = false
paste_key = "ctrl+v"

[models]
fast = "Systran/faster-whisper-small.en"
small = "Systran/faster-whisper-small.en"
cpu = "Systran/faster-whisper-small.en"
accuracy = "Systran/faster-whisper-large-v3-turbo"

[glossary]
enabled = true

[glossary.replacements]
"de-separation" = "d-separation"
"D separation" = "d-separation"
"d separation" = "d-separation"
latex = "LaTeX"
"bayesian network" = "Bayesian network"
"bayesian networks" = "Bayesian networks"

[shortcut]
device = "cuda"
model_tier = "cpu"
immediate = true
stop_on_silence = true
silence_seconds = 1.2
max_seconds = 30
min_seconds = 1
vad_threshold = 0.01
pre_speech_padding_ms = 200
post_speech_padding_ms = 300
```

Clipboard restore is off by default. If `restore_clipboard = true`, VoicePaste reads the current clipboard, pastes the transcript, then attempts to restore the previous clipboard content after paste.

## CUDA Notes

Keep `model_tier = "cpu"` or `model_tier = "small"` as the default until `voicepaste doctor` confirms CUDA works.

```bash
voicepaste transcribe-test --device cuda --tier cpu
voicepaste benchmark --device cuda --tier cpu
```

If CUDA is unavailable, use:

```bash
voicepaste --device cpu --model-tier cpu
```

## Troubleshooting

- Conda / `GLIBCXX`: if recording fails with a PortAudio/JACK error mentioning `GLIBCXX_3.4.32`, recreate `.venv` with `/usr/bin/python3`, deactivate Conda, and remove Miniconda/Anaconda paths from `LD_LIBRARY_PATH`.
- PortAudio/JACK: install `libportaudio2` and `portaudio19-dev`, then run `voicepaste record-test`.
- CUDA unavailable: run `voicepaste doctor`; if CUDA probes fail, use `--device cpu` until the NVIDIA driver and CTranslate2 CUDA support work.
- Wayland: focused insertion is compositor-dependent. Prefer clipboard fallback unless your compositor and tools support synthetic paste.
- X11 insertion: install `xdotool` and `xclip` or `xsel`.
- `xclip`: on X11, `xclip` intentionally remains alive as clipboard owner. VoicePaste starts it without waiting, so the CLI should not hang.
- Raw audio: temporary recordings are deleted by default. Test commands keep samples only when passed `--keep`.

## Development

```bash
/usr/bin/python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
python -m compileall src tests
pytest -q
```

Optional lint:

```bash
ruff check .
```

Hardware-facing commands:

```bash
voicepaste doctor
voicepaste record-test
voicepaste transcribe-test --seconds 5
voicepaste benchmark --seconds 8
voicepaste install-shortcut --dry-run
```

CI runs compile and unit tests only. It does not require a microphone, GPU, display server, CUDA, desktop insertion tools, or downloaded ASR models.

## Current Limitations

- Linux/Ubuntu is the first target.
- X11 insertion is validated; Wayland focused insertion is limited.
- ASR quality depends on the downloaded model, microphone, room noise, and hardware.
- No GUI, tray application, daemon, streaming transcription, cloud APIs, Ollama cleanup, or built-in global hotkey listener.

## License

MIT. See [LICENSE](LICENSE).
