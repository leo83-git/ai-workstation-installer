"""Registry for tool installers."""

from __future__ import annotations

from .antigravity import AntigravityInstaller
from .base import ToolInstaller
from .cursor import CursorInstaller
from .devin import DevinInstaller

REGISTRY: dict[str, type[ToolInstaller]] = {
    "antigravity": AntigravityInstaller,
    "cursor": CursorInstaller,
    "devin": DevinInstaller,
}
