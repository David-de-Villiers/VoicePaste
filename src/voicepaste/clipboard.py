from __future__ import annotations

"""Clipboard access wrappers for X11 and Wayland command-line tools."""

import shutil
import subprocess
import time


def available_clipboard_tools(session_type: str | None = None) -> list[str]:
    """Return installed clipboard tools in preferred order."""

    candidates = ["xclip", "xsel"] if session_type != "wayland" else ["wl-copy", "xclip", "xsel"]
    return [tool for tool in candidates if shutil.which(tool)]


def read_text(session_type: str | None = None) -> tuple[bool, str]:
    """Read text from the clipboard when a supported tool is available."""

    tools = available_clipboard_tools(session_type)
    for tool in tools:
        try:
            if tool == "xclip":
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2,
                )
                return True, proc.stdout
            if tool == "xsel":
                proc = subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2,
                )
                return True, proc.stdout
            if tool == "wl-copy":
                wl_paste = shutil.which("wl-paste")
                if not wl_paste:
                    continue
                proc = subprocess.run(
                    [wl_paste],
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2,
                )
                return True, proc.stdout
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return False, ""


def copy_text(text: str, session_type: str | None = None) -> tuple[bool, str]:
    """Copy text to the desktop clipboard without hanging on X11 owners."""

    tools = available_clipboard_tools(session_type)
    for tool in tools:
        try:
            if tool == "xclip":
                proc = subprocess.Popen(
                    ["xclip", "-selection", "clipboard"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
                assert proc.stdin is not None
                proc.stdin.write(text)
                proc.stdin.close()
                time.sleep(0.05)
                if proc.poll() not in {None, 0}:
                    stderr = proc.stderr.read() if proc.stderr else ""
                    raise RuntimeError(stderr.strip() or f"xclip exited with {proc.returncode}")
                return True, "copied with xclip"
            if tool == "xsel":
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text,
                    text=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                return True, "copied with xsel"
            if tool == "wl-copy":
                subprocess.run(
                    ["wl-copy"],
                    input=text,
                    text=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                return True, "copied with wl-copy"
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            last_error = f"{tool} failed: {exc}"
            continue
    if not tools:
        return False, "no clipboard tool found"
    return False, locals().get("last_error", "clipboard copy failed")
