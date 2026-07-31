"""Project constants."""

from .version import VERSION

STATE_FILE = "~/.local/share/aiws/state.json"
APP_NAME = "aiws"

__all__ = [
    "VERSION",
    "STATE_FILE",
    "APP_NAME",
]
