"""Installer orchestration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import StateManager
from .tools.base import ToolInstaller
from .tools.registry import REGISTRY


@dataclass
class InstallerManager:
    """Resolve and manage installer implementations."""

    state_manager: StateManager

    def create_installer(self, name: str) -> ToolInstaller:
        """Instantiate a registered installer by name."""

        installer_cls = REGISTRY.get(name)
        if installer_cls is None:
            raise KeyError(f"Unsupported tool: {name}")
        return installer_cls()

    def list_installed(self) -> list[dict[str, Any]]:
        """Return the recorded application state."""

        return self.state_manager.load().get("applications", [])

