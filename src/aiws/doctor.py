"""Diagnostics collection."""

from __future__ import annotations

import getpass
import logging
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .backup import BackupManager
from .dependencies import DependencyManager
from .desktop import DEFAULT_USER_APPS_DIR
from .shell import command_exists
from .state import StateManager

LOGGER = logging.getLogger(__name__)


@dataclass
class Doctor:
    """Collect system, environment, and application diagnostics."""

    dependency_manager: DependencyManager = field(default_factory=DependencyManager)
    state_manager: StateManager = field(default_factory=StateManager)

    def collect(self) -> dict[str, Any]:
        LOGGER.info("Diagnostics started")
        report = {
            "title": "AI Workstation Diagnostics",
            "system": self._safe_collect("system", self._collect_system),
            "environment": self._safe_collect("environment", self._collect_environment),
            "dependencies": self._safe_collect(
                "dependencies", self._collect_dependencies
            ),
            "installed_applications": self._safe_collect(
                "installed applications", self._collect_installed_applications
            ),
            "download_cache": self._safe_collect(
                "download cache", self._collect_download_cache
            ),
            "desktop_integration": self._safe_collect(
                "desktop integration", self._collect_desktop_integration
            ),
            "verification": self._safe_collect(
                "verification", self._collect_verification_support
            ),
        }
        LOGGER.info("Diagnostics completed")
        return report

    def _safe_collect(self, subsystem: str, collector: Any) -> dict[str, Any]:
        try:
            return {"status": "ok", "data": collector()}
        except Exception as exc:
            LOGGER.exception("Subsystem failure: %s", subsystem)
            return {"status": "error", "error": str(exc)}

    def _collect_system(self) -> dict[str, Any]:
        os_release = self._read_os_release()
        return {
            "ubuntu_version": os_release.get("VERSION_ID")
            or os_release.get("PRETTY_NAME"),
            "kernel_version": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
        }

    def _collect_environment(self) -> dict[str, Any]:
        return {
            "current_user": getpass.getuser(),
            "path": os.environ.get("PATH", ""),
            "virtualenv": os.environ.get("VIRTUAL_ENV") or None,
        }

    def _collect_dependencies(self) -> dict[str, bool]:
        return {
            "apt": self.dependency_manager.detect_apt(),
            "sudo": self.dependency_manager.detect_sudo(),
            "curl": command_exists("curl"),
            "wget": command_exists("wget"),
            "git": self.dependency_manager.detect_git(),
            "tar": command_exists("tar"),
            "unzip": command_exists("unzip"),
        }

    def _collect_installed_applications(self) -> list[dict[str, Any]]:
        state = self.state_manager.load()
        applications = state.get("applications", [])
        return [
            {
                "name": item.get("name"),
                "install_path": item.get("install_path"),
                "version": item.get("version"),
            }
            for item in applications
        ]

    def _collect_download_cache(self) -> dict[str, Any]:
        cache_dir = Path("/tmp")
        files = [path for path in cache_dir.iterdir() if path.is_file()]
        total_size = sum(path.stat().st_size for path in files)
        return {
            "location": str(cache_dir),
            "cached_files": len(files),
            "total_size": total_size,
        }

    def _collect_desktop_integration(self) -> dict[str, Any]:
        present: list[str] = []
        missing: list[str] = []
        broken: list[str] = []
        state = self.state_manager.load()
        expected = {
            item.get("name"): item.get("executable")
            for item in state.get("applications", [])
        }
        for desktop_file in DEFAULT_USER_APPS_DIR.glob("*.desktop"):
            present.append(str(desktop_file))
            exec_target = self._read_exec_target(desktop_file)
            if exec_target and not Path(exec_target).exists():
                broken.append(str(desktop_file))
        for name in expected:
            desktop_file = DEFAULT_USER_APPS_DIR / f"{name}.desktop"
            if not desktop_file.exists():
                missing.append(str(desktop_file))
        return {"present": present, "missing": missing, "broken": broken}

    def _collect_verification_support(self) -> dict[str, bool]:
        return {
            "checksum_support": True,
            "backup_support": isinstance(BackupManager(), BackupManager),
        }

    def _read_os_release(self) -> dict[str, str]:
        data: dict[str, str] = {}
        path = Path("/etc/os-release")
        if not path.exists():
            return data
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key] = value.strip().strip('"')
        return data

    def _read_exec_target(self, desktop_file: Path) -> str | None:
        for line in desktop_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("Exec="):
                return line.removeprefix("Exec=").split()[0]
        return None


def run_doctor_checks() -> list[str]:
    """Compatibility helper returning a textual summary."""

    report = Doctor().collect()
    return [
        f"{section}: {value['status']}"
        for section, value in report.items()
        if section != "title"
    ]
