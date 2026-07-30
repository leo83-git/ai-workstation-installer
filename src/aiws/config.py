"""Configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .constants import STATE_FILE


@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""

    state_file: Path = field(default_factory=lambda: Path(STATE_FILE).expanduser())
