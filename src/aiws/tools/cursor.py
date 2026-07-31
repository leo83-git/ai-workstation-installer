"""Cursor installer implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiws.shell import command_exists, run, run_sudo

from .base import BaseInstaller

DEFAULT_CURSOR_DEB = Path("/tmp/cursor.deb")
DEFAULT_EXECUTABLE = Path("/usr/bin/cursor")
DEFAULT_DESKTOP_FILE = Path("/usr/share/applications/cursor.desktop")
DEFAULT_INSTALL_DIR = Path("/opt/Cursor")
DEFAULT_PACKAGE_NAME = "cursor"


@dataclass(frozen=True)
class CursorDetection:
    """Structured detection data for Cursor."""

    executable_exists: bool
    installation_directory_exists: bool
    desktop_file_exists: bool
    version: str | None

    @property
    def installed(self) -> bool:
        return self.executable_exists or self.installation_directory_exists


@dataclass(frozen=True)
class CursorInstallationRecord:
    """Persisted Cursor installation details."""

    name: str = DEFAULT_PACKAGE_NAME
    install_path: str = str(DEFAULT_INSTALL_DIR)
    executable: str = str(DEFAULT_EXECUTABLE)
    version: str | None = None
    installation_type: str = "deb"


@dataclass(frozen=True)
class CursorDoctorReport:
    """Structured diagnostics for Cursor."""

    name: str
    executable_exists: bool
    desktop_launcher_exists: bool
    version_available: bool
    state_matches_filesystem: bool
    recorded_state: dict[str, Any] | None


@dataclass
class CursorInstaller(BaseInstaller):
    """Installer for the Cursor editor."""

    package_path: Path = DEFAULT_CURSOR_DEB
    executable_path: Path = DEFAULT_EXECUTABLE
    desktop_file: Path = DEFAULT_DESKTOP_FILE
    install_dir: Path = DEFAULT_INSTALL_DIR
    name: str = DEFAULT_PACKAGE_NAME

    def detect(self) -> CursorDetection:
        return CursorDetection(
            executable_exists=self._detect_executable(),
            installation_directory_exists=self._detect_install_directory(),
            desktop_file_exists=self._detect_desktop_file(),
            version=self._read_version(),
        )

    def update(self) -> str:
        version = self.detect().version or "unknown"
        message = f"Cursor update is not implemented yet. Current version: {version}"
        self.logger.info(message)
        return message

    def doctor(self) -> CursorDoctorReport:
        detection = self.detect()
        state = self.state_manager.load()
        applications = state.get("applications", [])
        recorded = next(
            (item for item in applications if item.get("name") == DEFAULT_PACKAGE_NAME),
            None,
        )
        diagnostics = CursorDoctorReport(
            name=DEFAULT_PACKAGE_NAME,
            executable_exists=detection.executable_exists,
            desktop_launcher_exists=detection.desktop_file_exists,
            version_available=detection.version is not None,
            state_matches_filesystem=bool(recorded) and detection.executable_exists,
            recorded_state=recorded,
        )
        self.logger.info("Cursor diagnostics collected")
        return diagnostics

    def install_package(self) -> None:
        self.logger.info("Installing Cursor package from %s", self.package_path)
        run_sudo(["apt", "install", "-y", str(self.package_path)], check=True)

    def _record_state(self, detection: CursorDetection) -> None:
        record = CursorInstallationRecord(version=detection.version)
        self.state_manager.load()
        self.state_manager.state["applications"] = [
            item
            for item in self.state_manager.list_installed()
            if item.get("name") != DEFAULT_PACKAGE_NAME
        ]
        self.state_manager.record_application(record.__dict__)

    def validate_input(self) -> None:
        self.logger.info("Validating Cursor package input")
        architecture = self._detect_architecture()
        if architecture not in {"amd64", "arm64"}:
            raise RuntimeError(f"Unsupported architecture: {architecture}")
        super().validate_input()

    def verify_package(self) -> None:
        self.logger.info("Verifying Cursor package availability")
        super().verify_package()

    def _detect_architecture(self) -> str:
        result = run(["dpkg", "--print-architecture"], check=True)
        return result.stdout.strip() or "unknown"

    def _detect_executable(self) -> bool:
        return command_exists(self.executable_path.name)

    def _detect_install_directory(self) -> bool:
        return self.install_dir.exists()

    def _detect_desktop_file(self) -> bool:
        return self.desktop_file.exists()

    def _read_version(self) -> str | None:
        if not command_exists(self.executable_path.name):
            return None
        result = run([str(self.executable_path), "--version"], check=False)
        if result.returncode != 0:
            return None
        return self._extract_version(result.stdout)

    @staticmethod
    def _extract_version(output: str) -> str | None:
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
        return match.group(1) if match else output.strip() or None
