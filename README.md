# VoicePaste

VoicePaste is a terminal-first, local/offline Linux dictation utility. It records from the default microphone, transcribes with a local `faster-whisper` model, and pastes the result into the focused application when the desktop allows it.

No audio, transcript, correction request, telemetry, or log is sent to a cloud service by the app. Model download is the only networked setup step.

## Validated Target

This MVP has been validated on Ubuntu 24.04 with X11 (`DISPLAY=:1`), PipeWire audio, `xdotool` insertion, and `xclip`/`xsel` clipboard fallback. CPU transcription works with `Systran/faster-whisper-small.en` using int8. CUDA transcription works on the validated machine when run from the real user session.

## CPU-First Install

Use the system Python venv, not Conda. Conda's `libstdc++` can break PortAudio/JACK loading on Ubuntu.

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev ffmpeg libportaudio2 portaudio19-dev libnotify-bin xdotool xclip xsel
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

## Use

```bash
voicepaste
voicepaste --copy-only
voicepaste --no-paste
voicepaste --language en --model-tier cpu --device cpu
voicepaste paste-last
```

The default flow is press Enter to start, press Enter again to stop, transcribe, print the final transcript, then paste. If focused insertion is unavailable, VoicePaste copies to the clipboard when possible, prints the transcript, sends a desktop notification, and stores it as the last transcript.

`--copy-only` and `--no-paste` record, transcribe, print, and copy without calling `xdotool`.

## Test Commands

```bash
voicepaste doctor
voicepaste record-test
voicepaste transcribe-test --seconds 5
voicepaste benchmark --seconds 8
pytest -q
```

## Config

Config is stored at `~/.config/voicepaste/config.toml`.

```toml
backend = "faster-whisper"
model_tier = "cpu"
language = "en"
record_sample_rate = 16000
max_record_seconds = 120
delete_audio = true

[insertion]
prefer_clipboard_paste = true
restore_clipboard = false
paste_key = "ctrl+v"

[models]
fast = "Systran/faster-whisper-small.en"
cpu = "Systran/faster-whisper-small.en"
accuracy = "Systran/faster-whisper-large-v3-turbo"
```

Clipboard restore is off by default. If `restore_clipboard = true`, VoicePaste reads the current clipboard, pastes the transcript, then attempts to restore the previous clipboard content after paste.

## CUDA Notes

Keep `model_tier = "cpu"` as the default until `voicepaste doctor` confirms CUDA works. Use explicit overrides when testing:

```bash
voicepaste transcribe-test --device cuda --tier cpu
voicepaste benchmark --device cuda --tier cpu
```

For higher accuracy after CUDA is confirmed:

```bash
voicepaste models fetch --tier accuracy
voicepaste benchmark --device cuda --tier accuracy
```

## Troubleshooting

- If `record-test` fails with a PortAudio/JACK error mentioning `GLIBCXX_3.4.32`, recreate `.venv` with `/usr/bin/python3`, deactivate Conda, and remove Miniconda/Anaconda paths from `LD_LIBRARY_PATH`.
- If `doctor` warns that Conda base is active, run `conda deactivate` before launching VoicePaste.
- If `record-test` cannot see audio devices from an isolated shell, run it from the real desktop user session where PipeWire is available.
- X11 insertion requires `xdotool` plus `xclip` or `xsel`.
- `xclip` intentionally remains alive as the clipboard owner on X11. VoicePaste starts it without waiting, so the CLI should not hang.
- Wayland support is diagnostic-first in this MVP. Compositor restrictions can prevent synthetic typing or focus detection, so clipboard fallback is expected.
- Raw audio is written to temporary files and deleted by default. Test commands keep samples only when passed `--keep`.
