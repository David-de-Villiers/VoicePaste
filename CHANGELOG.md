# Changelog

## 0.1.0 - Initial Public Release

- Local/offline dictation CLI for Linux.
- Records microphone audio locally and transcribes with `faster-whisper`.
- Supports CPU and CUDA transcription when available.
- Inserts text into focused X11 applications via clipboard plus `xdotool`.
- Provides clipboard fallback, desktop notifications, and `paste-last`.
- Adds technical dictation glossary and initial prompt support.
- Adds GNOME shortcut-friendly immediate recording with RMS silence detection.
- Includes diagnostics, benchmark, record/transcribe test, quality-test, and compare-models commands.
