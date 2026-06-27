# VoicePaste Architecture

VoicePaste is intentionally split into small modules so recording, transcription, desktop insertion, and CLI concerns can evolve independently.

## Runtime Flow

1. `voicepaste.cli` parses options and chooses either the interactive terminal recorder or shortcut-friendly immediate recorder.
2. `voicepaste.audio` records local microphone audio to a temporary WAV file.
3. `voicepaste.transcribe` loads a locally cached faster-whisper model and transcribes the WAV file.
4. `voicepaste.postprocess` normalizes whitespace and applies deterministic glossary replacements.
5. `voicepaste.state` stores the final transcript as local `paste-last` state.
6. `voicepaste.insert` copies text to the clipboard and attempts focused-window paste.
7. `voicepaste.clipboard` handles X11/Wayland clipboard tools.
8. `voicepaste.notify` sends best-effort desktop notifications.

## Module Boundaries

- `audio.py`: microphone capture, WAV writing, WAV inspection, silence calibration.
- `vad.py`: pure RMS-based silence detection that can be unit tested with synthetic arrays.
- `transcribe.py`: local ASR backend selection and faster-whisper invocation.
- `models.py`: model cache paths and setup-time model download.
- `postprocess.py`: transcript cleanup and glossary replacements.
- `insert.py`: desktop session detection and paste simulation.
- `clipboard.py`: command-line clipboard integration.
- `diagnostics.py`: environment and dependency checks for `voicepaste doctor`.
- `config.py`: XDG paths, defaults, and typed config dataclasses.
- `cli.py`: command-line interface and orchestration.

## Privacy Invariants

- Audio and transcription are local after model download.
- Raw audio is written only to temporary files and deleted by default.
- `paste-last` state stores only the final transcript locally.
- No cloud ASR, telemetry, remote correction, or hosted logging is called by the app.

## Testing Strategy

Hardware-facing behavior is kept behind module boundaries. Unit tests use synthetic audio arrays and mocks for clipboard, insertion, recording, and transcription so CI does not require a microphone, GPU, display server, or downloaded model.
