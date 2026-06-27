from __future__ import annotations

"""Environment and dependency diagnostics for `voicepaste doctor`."""

from dataclasses import dataclass
from importlib import metadata
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from .config import Config, config_path, model_dir
from .insert import insertion_capability
from .models import model_local_path


@dataclass(frozen=True)
class Check:
    """One diagnostic check result."""

    name: str
    value: str
    ok: bool | None = None


def _run(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8, check=False)
        return proc.returncode, proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def _which(name: str) -> str:
    return shutil.which(name) or "missing"


def _version(package: str, module: str | None = None) -> tuple[str, bool]:
    module = module or package.replace("-", "_")
    if not importlib.util.find_spec(module):
        return "missing", False
    try:
        return metadata.version(package), True
    except metadata.PackageNotFoundError:
        return "installed; version unknown", True


def _active_conda_warning(env: dict[str, str] | None = None) -> Check:
    env = os.environ if env is None else env
    conda_env = env.get("CONDA_DEFAULT_ENV", "")
    conda_prefix = env.get("CONDA_PREFIX", "")
    if conda_env == "base":
        return Check("Conda", f"base active at {conda_prefix or 'unknown prefix'}", False)
    if conda_env or conda_prefix:
        return Check("Conda", f"active env {conda_env or 'unknown'} at {conda_prefix or 'unknown prefix'}", False)
    return Check("Conda", "not active", True)


def _ld_library_path_warning(env: dict[str, str] | None = None) -> Check:
    env = os.environ if env is None else env
    value = env.get("LD_LIBRARY_PATH", "")
    lowered = value.lower()
    if "miniconda" in lowered or "anaconda" in lowered or "conda" in lowered:
        return Check("LD_LIBRARY_PATH", f"contains Conda path: {value}", False)
    return Check("LD_LIBRARY_PATH", value or "unset", True)


def _running_from_project_venv() -> Check:
    expected = Path.cwd() / ".venv"
    actual = Path(sys.prefix)
    try:
        return Check("Project venv", str(actual), actual.resolve() == expected.resolve())
    except OSError:
        return Check("Project venv", str(actual), False)


def collect_diagnostics(cfg: Config) -> list[Check]:
    """Collect hardware, desktop, dependency, and model diagnostics."""

    checks: list[Check] = []
    checks.append(Check("OS", platform.platform(), True))
    checks.append(Check("Python", sys.version.split()[0], sys.version_info >= (3, 11)))
    checks.append(Check("Python executable", sys.executable, True))
    checks.append(_running_from_project_venv())
    checks.append(_active_conda_warning())
    checks.append(_ld_library_path_warning())
    checks.append(Check("Config", str(config_path()), config_path().exists()))
    checks.append(Check("Model directory", str(model_dir()), model_dir().exists()))
    checks.append(Check("Privacy", "offline transcription; no telemetry; raw temp audio deleted by default", True))

    code, out = _run(["nvidia-smi"])
    first_line = out.splitlines()[0] if out else "no output"
    checks.append(Check("nvidia-smi", first_line, code == 0))

    code, out = _run(["lspci", "-nn"])
    gpu_lines = []
    for line in out.splitlines():
        lower = line.lower()
        if "vga compatible controller" in lower or "3d controller" in lower or "display controller" in lower or "nvidia" in lower:
            gpu_lines.append(line)
    checks.append(Check("GPU PCI", " | ".join(gpu_lines) if gpu_lines else "not found", code == 0 and bool(gpu_lines)))

    ctranslate_version, ctranslate_ok = _version("ctranslate2")
    checks.append(Check("ctranslate2", ctranslate_version, ctranslate_ok))
    if importlib.util.find_spec("ctranslate2"):
        try:
            import ctranslate2

            cuda_types = sorted(ctranslate2.get_supported_compute_types("cuda"))
            checks.append(Check("CUDA Python", ", ".join(cuda_types) if cuda_types else "no CUDA compute types", bool(cuda_types)))
        except Exception as exc:
            checks.append(Check("CUDA Python", f"ctranslate2 CUDA probe failed: {exc}", False))
    else:
        checks.append(Check("CUDA Python", "ctranslate2 missing", False))
    faster_version, faster_ok = _version("faster-whisper", "faster_whisper")
    sounddevice_version, sounddevice_ok = _version("sounddevice")
    checks.append(Check("faster-whisper", faster_version, faster_ok))
    checks.append(Check("sounddevice", sounddevice_version, sounddevice_ok))

    session = os.environ.get("XDG_SESSION_TYPE") or ("wayland" if os.environ.get("WAYLAND_DISPLAY") else "x11" if os.environ.get("DISPLAY") else "unknown")
    checks.append(Check("Desktop session", session, session in {"x11", "wayland"}))
    checks.append(Check("DISPLAY", os.environ.get("DISPLAY", "unset"), bool(os.environ.get("DISPLAY"))))
    checks.append(Check("WAYLAND_DISPLAY", os.environ.get("WAYLAND_DISPLAY", "unset"), None))

    code, out = _run(["arecord", "-L"])
    checks.append(Check("Audio default", "default capture listed" if "default" in out else "default capture not listed", "default" in out))
    checks.append(Check("ffmpeg", _which("ffmpeg"), bool(shutil.which("ffmpeg"))))
    checks.append(Check("notify-send", _which("notify-send"), bool(shutil.which("notify-send"))))

    cap = insertion_capability()
    checks.append(Check("Insertion", str(cap["reason"]), bool(cap["can_paste"])))
    tools = cap["tools"]
    for name in ["xdotool", "xclip", "xsel", "wl-copy", "wtype", "ydotool"]:
        checks.append(Check(name, _which(name), bool(tools.get(name))))

    model_id = cfg.model_id_for_tier()
    local_model = model_local_path(model_id)
    checks.append(Check("Backend", cfg.backend, cfg.backend == "faster-whisper"))
    checks.append(Check("Model tier", cfg.model_tier, cfg.model_tier in {"fast", "small", "cpu", "accuracy"}))
    checks.append(Check("Model", f"{model_id} -> {local_model}", local_model.exists()))
    if local_model.exists() and faster_ok:
        try:
            from faster_whisper import WhisperModel

            WhisperModel(str(local_model), device="cpu", compute_type="int8")
            checks.append(Check("faster-whisper CPU probe", "local model load ok", True))
        except Exception as exc:
            checks.append(Check("faster-whisper CPU probe", str(exc), False))
        try:
            from faster_whisper import WhisperModel

            WhisperModel(str(local_model), device="cuda", compute_type="float16")
            checks.append(Check("faster-whisper CUDA probe", "local model load ok", True))
        except Exception as exc:
            checks.append(Check("faster-whisper CUDA probe", str(exc), False))
    return checks


def format_checks(checks: list[Check]) -> str:
    """Format diagnostic checks for terminal output."""

    lines = []
    for check in checks:
        marker = "?"
        if check.ok is True:
            marker = "OK"
        elif check.ok is False:
            marker = "WARN"
        lines.append(f"{marker:4} {check.name}: {check.value}")
    return "\n".join(lines)
