from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

from . import __version__
from . import audio
from .config import load_config, write_default_config
from .diagnostics import collect_diagnostics, format_checks
from .insert import insert_or_copy
from .models import fetch_model
from .notify import notify
from .postprocess import cleanup_text
from .state import read_last_transcript, save_last_transcript
from .transcribe import transcribe_file


FALLBACK_MESSAGE = "No text field detected. Click where you want the text, then paste."


@dataclass(frozen=True)
class RuntimeOptions:
    paste: bool = True
    quiet: bool = False
    language: str | None = None
    model_tier: str | None = None
    device: str = "auto"


def _runtime_options(args: argparse.Namespace) -> RuntimeOptions:
    no_paste = bool(getattr(args, "no_paste", False))
    copy_only = bool(getattr(args, "copy_only", False))
    return RuntimeOptions(
        paste=not (no_paste or copy_only),
        quiet=bool(getattr(args, "quiet", False)),
        language=getattr(args, "language", None),
        model_tier=getattr(args, "model_tier", None) or getattr(args, "tier", None),
        device=getattr(args, "device", "auto"),
    )


def _handle_transcript(text: str, options: RuntimeOptions | None = None) -> int:
    options = options or RuntimeOptions()
    cfg = load_config()
    text = cleanup_text(text)
    save_last_transcript(text)
    if not options.quiet:
        print(text)
    if options.paste:
        result = insert_or_copy(text, cfg.insertion)
        if not result.inserted:
            notify(FALLBACK_MESSAGE)
        if result.inserted:
            print(f"[voicepaste] inserted ({result.message})", file=sys.stderr)
        elif result.copied:
            print(f"[voicepaste] copied fallback ({result.message})", file=sys.stderr)
        else:
            print(f"[voicepaste] fallback without clipboard ({result.message})", file=sys.stderr)
        return 0
    from .clipboard import copy_text
    from .insert import session_type

    copied, message = copy_text(text, session_type())
    if copied:
        print(f"[voicepaste] copied ({message}); paste skipped", file=sys.stderr)
    else:
        print(f"[voicepaste] clipboard unavailable ({message}); paste skipped", file=sys.stderr)
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    write_default_config()
    cfg = load_config()
    print(format_checks(collect_diagnostics(cfg)))
    return 0


def cmd_record_test(args: argparse.Namespace) -> int:
    cfg = load_config()
    path = audio.record_fixed(args.seconds, cfg.record_sample_rate)
    try:
        stats = audio.validate_audio(path)
        print(f"Recorded {stats.duration_seconds:.2f}s, rms={stats.rms:.6f}, sample_rate={stats.sample_rate}, path={path}")
        if args.play:
            import subprocess

            subprocess.run(["aplay", str(path)], check=False)
        return 0
    finally:
        if not args.keep and path.exists():
            path.unlink()


def cmd_transcribe_test(args: argparse.Namespace) -> int:
    cfg = load_config()
    options = _runtime_options(args)
    path = Path(args.file) if args.file else audio.record_fixed(args.seconds, cfg.record_sample_rate)
    owned = args.file is None
    try:
        audio.validate_audio(path, min_rms=0.0)
        result = transcribe_file(path, cfg, tier=options.model_tier, device=options.device, language=options.language)
        print(cleanup_text(result.text))
        print(
            f"[voicepaste] backend={result.backend} device={result.device} compute={result.compute_type} "
            f"elapsed={result.duration_seconds:.2f}s model={result.model_path}",
            file=sys.stderr,
        )
        return 0
    finally:
        if owned and not args.keep and path.exists():
            path.unlink()


def cmd_benchmark(args: argparse.Namespace) -> int:
    cfg = load_config()
    options = _runtime_options(args)
    path = Path(args.file) if args.file else audio.record_fixed(args.seconds, cfg.record_sample_rate)
    owned = args.file is None
    try:
        stats = audio.inspect_wav(path)
        result = transcribe_file(path, cfg, tier=options.model_tier, device=options.device, language=options.language)
        rtf = result.duration_seconds / stats.duration_seconds if stats.duration_seconds else 0.0
        print(f"audio_seconds={stats.duration_seconds:.2f}")
        print(f"transcribe_seconds={result.duration_seconds:.2f}")
        print(f"realtime_factor={rtf:.2f}")
        print(f"backend={result.backend}")
        print(f"device={result.device}")
        print(f"compute_type={result.compute_type}")
        print(f"model={result.model_path}")
        return 0
    finally:
        if owned and not args.keep and path.exists():
            path.unlink()


def cmd_paste_last(args: argparse.Namespace) -> int:
    text = read_last_transcript()
    if not text:
        print("No last transcript found.", file=sys.stderr)
        return 1
    return _handle_transcript(text, _runtime_options(args))


def cmd_models_fetch(args: argparse.Namespace) -> int:
    cfg = load_config()
    path = fetch_model(cfg, args.tier)
    print(path)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config()
    options = _runtime_options(args)
    path = audio.record_until_enter(cfg.record_sample_rate, cfg.max_record_seconds)
    try:
        stats = audio.validate_audio(path)
        print(f"[voicepaste] captured {stats.duration_seconds:.2f}s; transcribing...", file=sys.stderr)
        result = transcribe_file(path, cfg, tier=options.model_tier, device=options.device, language=options.language)
        return _handle_transcript(result.text, options)
    finally:
        if cfg.delete_audio and path.exists():
            path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voicepaste")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-paste", action="store_true", help="copy and print transcript without simulating paste")
    parser.add_argument("--copy-only", action="store_true", help="copy and print transcript without simulating paste")
    parser.add_argument("--quiet", action="store_true", help="do not print the final transcript")
    parser.add_argument("--language", default=None, help="transcription language override, for example en")
    parser.add_argument("--model-tier", choices=["fast", "cpu", "accuracy"], help="model tier override")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto", help="transcription device override")
    sub = parser.add_subparsers(dest="command")

    doctor = sub.add_parser("doctor", help="report local hardware, desktop, audio, and ASR capability")
    doctor.set_defaults(func=cmd_doctor)

    record = sub.add_parser("record-test", help="record and validate a short local sample")
    record.add_argument("--seconds", type=float, default=3.0)
    record.add_argument("--keep", action="store_true")
    record.add_argument("--play", action="store_true")
    record.set_defaults(func=cmd_record_test)

    transcribe = sub.add_parser("transcribe-test", help="record or transcribe a local test sample")
    transcribe.add_argument("--file")
    transcribe.add_argument("--seconds", type=float, default=4.0)
    transcribe.add_argument("--tier", choices=["fast", "cpu", "accuracy"])
    transcribe.add_argument("--language", default=None)
    transcribe.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    transcribe.add_argument("--keep", action="store_true")
    transcribe.set_defaults(func=cmd_transcribe_test)

    bench = sub.add_parser("benchmark", help="measure local transcription speed")
    bench.add_argument("--file")
    bench.add_argument("--seconds", type=float, default=8.0)
    bench.add_argument("--tier", choices=["fast", "cpu", "accuracy"])
    bench.add_argument("--language", default=None)
    bench.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    bench.add_argument("--keep", action="store_true")
    bench.set_defaults(func=cmd_benchmark)

    paste_last = sub.add_parser("paste-last", help="paste or copy the last transcript")
    paste_last.add_argument("--no-paste", action="store_true", help="copy and print without simulating paste")
    paste_last.add_argument("--copy-only", action="store_true", help="copy and print without simulating paste")
    paste_last.add_argument("--quiet", action="store_true", help="do not print the final transcript")
    paste_last.set_defaults(func=cmd_paste_last)

    models = sub.add_parser("models")
    models_sub = models.add_subparsers(dest="models_command", required=True)
    fetch = models_sub.add_parser("fetch", help="download a model for offline use")
    fetch.add_argument("--tier", required=True, choices=["fast", "cpu", "accuracy"])
    fetch.set_defaults(func=cmd_models_fetch)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if not hasattr(args, "func"):
            return cmd_run(args)
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"voicepaste: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
