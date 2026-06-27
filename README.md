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
voicepaste --language en --model-tier small --device cuda
voicepaste paste-last
voicepaste quality-test --seconds 10 --device cuda --model-tier small
voicepaste compare-models --tiers fast,small,accuracy --seconds 10 --device cuda
```

The default flow is press Enter to start, press Enter again to stop, transcribe, print the final transcript, then paste. If focused insertion is unavailable, VoicePaste copies to the clipboard when possible, prints the transcript, sends a desktop notification, and stores it as the last transcript.

`--copy-only` and `--no-paste` record, transcribe, print, and copy without calling `xdotool`.

For technical writing, use `quality-test` to see both the raw ASR output and the final glossary-corrected output:

```bash
voicepaste quality-test --seconds 10 --device cuda --model-tier small
```

Example glossary correction:

```text
raw_transcript=... de-separation and latex ...
final_transcript=... d-separation and LaTeX ...
```

Use `compare-models` to record once and run the same audio through several tiers:

```bash
voicepaste compare-models --tiers fast,cpu --seconds 10 --device cuda
```

## Test Commands

```bash
voicepaste doctor
voicepaste record-test
voicepaste transcribe-test --seconds 5
voicepaste benchmark --seconds 8
voicepaste quality-test --seconds 10 --device cuda --model-tier cpu
voicepaste compare-models --tiers fast,cpu --seconds 10 --device cuda
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
```

Clipboard restore is off by default. If `restore_clipboard = true`, VoicePaste reads the current clipboard, pastes the transcript, then attempts to restore the previous clipboard content after paste.

## Technical Dictation

VoicePaste uses two local, deterministic quality aids:

- `initial_prompt` is passed to faster-whisper to bias recognition toward technical terms such as Bayesian networks, conditional independence, d-separation, expected utility, and LaTeX.
- `[glossary.replacements]` runs after ASR to fix common recurring terms without an LLM or network call.

Glossary replacements are case-insensitive and deterministic. They are intended for known terms, not broad grammar correction.

Model tier and device are separate:

- `--model-tier` selects the ASR model size/profile.
- `--device` selects where inference runs: `cpu`, `cuda`, or `auto`.
- `cpu` is retained as a backward-compatible tier alias for the original small CPU-safe model. Prefer `small` in new commands and configs.

On the validated RTX 3070 Ti Laptop GPU, recommended day-to-day technical dictation settings are:

```bash
voicepaste --device cuda --model-tier small
```

For more accuracy when latency is acceptable:

```bash
voicepaste models fetch --tier accuracy
voicepaste --device cuda --model-tier accuracy
```

## CUDA Notes

Keep `model_tier = "cpu"` or `model_tier = "small"` as the default until `voicepaste doctor` confirms CUDA works. Use explicit overrides when testing:

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
