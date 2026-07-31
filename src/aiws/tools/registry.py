"""Registry for tool installers."""

from __future__ import annotations

from .base import ToolInstaller
from .cursor import CursorInstaller
from .devin import DevinInstaller

REGISTRY: dict[str, type[ToolInstaller]] = {
    "cursor": CursorInstaller,
    "devin": DevinInstaller,
}
