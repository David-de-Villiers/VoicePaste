"""VoicePaste local/offline dictation CLI."""

from importlib import metadata

try:
    __version__ = metadata.version("voicepaste")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"
