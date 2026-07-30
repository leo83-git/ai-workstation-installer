"""Persistent application state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import STATE_FILE
from .filesystem import read_json, write_json


@dataclass
class StateManager:
    """Manage installer state on disk."""

    state_path: Path = field(default_factory=lambda: Path(STATE_FILE).expanduser())
    state: dict[str, Any] = field(default_factory=lambda: {"applications": []})

    def load(self) -> dict[str, Any]:
        if self.state_path.exists():
            self.state = read_json(self.state_path)
        return self.state

    def save(self) -> None:
        write_json(self.state_path, self.state)

    def list_installed(self) -> list[dict[str, Any]]:
        return list(self.state.get("applications", []))

    def record_application(self, application: dict[str, Any]) -> None:
        applications = self.state.setdefault("applications", [])
        applications.append(application)
        self.save()

    def remove_application(self, name: str) -> None:
        applications = self.state.setdefault("applications", [])
        self.state["applications"] = [
            item for item in applications if item.get("name") != name
        ]
        self.save()
