"""Registry for future tool installers."""

from __future__ import annotations

from .base import ToolInstaller

REGISTRY: dict[str, type[ToolInstaller]] = {}
