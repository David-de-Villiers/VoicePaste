---
name: voicepaste-local-asr
description: Use when planning or implementing VoicePaste, a local offline Linux voice transcription CLI that records audio, transcribes locally, and inserts or copies text into the active application.
---

Project-specific rules:

- Keep all transcription and post-processing local and offline.
- Do not use cloud APIs, hosted telemetry, or remote model calls.
- Inspect hardware before choosing ASR backend or model.
- Prefer a minimal terminal-first MVP before hotkeys, tray UI, streaming, or daemon mode.
- Treat X11 and Wayland differently. Do not assume focused text insertion is always possible.
- Always provide clipboard fallback and terminal output.
- Avoid storing raw audio by default.
- Keep modules separated: audio capture, VAD, transcription, post-processing, insertion, clipboard, diagnostics, config, CLI.
- Provide `voicepaste doctor`, `voicepaste record-test`, `voicepaste transcribe-test`, `voicepaste paste-last`, and a normal `voicepaste` flow.
