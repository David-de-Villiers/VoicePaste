from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
import time

from . import clipboard
from .config import InsertionConfig


@dataclass(frozen=True)
class InsertResult:
    inserted: bool
    copied: bool
    message: str


def session_type() -> str:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() or ("wayland" if os.environ.get("WAYLAND_DISPLAY") else "x11")


def insertion_capability() -> dict[str, object]:
    stype = session_type()
    tools = {
        "xdotool": bool(shutil.which("xdotool")),
        "wtype": bool(shutil.which("wtype")),
        "ydotool": bool(shutil.which("ydotool")),
        "xclip": bool(shutil.which("xclip")),
        "xsel": bool(shutil.which("xsel")),
        "wl-copy": bool(shutil.which("wl-copy")),
    }
    can_paste = False
    reason = ""
    if stype == "x11":
        can_paste = tools["xdotool"] and (tools["xclip"] or tools["xsel"])
        reason = "X11 clipboard paste available" if can_paste else "install xdotool and xclip or xsel"
    elif stype == "wayland":
        can_paste = tools["wtype"] and tools["wl-copy"]
        reason = "Wayland wtype paste available" if can_paste else "Wayland compositor may block insertion; use clipboard fallback"
    else:
        reason = "unknown desktop session"
    return {"session": stype, "tools": tools, "can_paste": can_paste, "reason": reason}


def _simulate_paste(stype: str, paste_key: str) -> tuple[bool, str]:
    try:
        if stype == "x11" and shutil.which("xdotool"):
            subprocess.run(["xdotool", "key", "--clearmodifiers", paste_key], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True, "pasted with xdotool"
        if stype == "wayland" and shutil.which("wtype"):
            keys = paste_key.lower().replace("ctrl", "ctrl").split("+")
            if keys == ["ctrl", "v"]:
                subprocess.run(["wtype", "-M", "ctrl", "v", "-m", "ctrl"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                return True, "pasted with wtype"
            return False, f"unsupported Wayland paste key: {paste_key}"
        return False, "no paste simulation tool found"
    except (OSError, subprocess.CalledProcessError) as exc:
        return False, f"paste simulation failed: {exc}"


def insert_or_copy(text: str, cfg: InsertionConfig | None = None) -> InsertResult:
    cfg = cfg or InsertionConfig()
    stype = session_type()
    previous_clipboard: str | None = None
    if cfg.restore_clipboard:
        ok, previous = clipboard.read_text(stype)
        if ok:
            previous_clipboard = previous
    copied, copy_msg = clipboard.copy_text(text, stype)
    if not copied:
        return InsertResult(False, False, copy_msg)
    paste_ok, paste_msg = _simulate_paste(stype, cfg.paste_key)
    if paste_ok:
        time.sleep(0.05)
        if previous_clipboard is not None:
            clipboard.copy_text(previous_clipboard, stype)
        return InsertResult(True, True, paste_msg)
    return InsertResult(False, True, paste_msg)
