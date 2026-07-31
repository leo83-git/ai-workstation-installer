"""Cursor installer implementation."""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiws.dependencies import DependencyManager
from aiws.filesystem import remove_path
from aiws.shell import command_exists, run, run_sudo
from aiws.state import StateManager

from .base import ToolInstaller

LOGGER = logging.getLogger(__name__)

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
        """Return whether Cursor appears installed."""

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
class CursorInstaller(ToolInstaller):
    """Installer for the Cursor editor."""

    package_path: Path = DEFAULT_CURSOR_DEB
    dependency_manager: DependencyManager = field(default_factory=DependencyManager)
    state_manager: StateManager = field(default_factory=StateManager)
    executable_path: Path = DEFAULT_EXECUTABLE
    desktop_file: Path = DEFAULT_DESKTOP_FILE
    install_dir: Path = DEFAULT_INSTALL_DIR

    def detect(self) -> CursorDetection:
        """Detect whether Cursor is installed and gather details."""

        return CursorDetection(
            executable_exists=self._detect_executable(),
            installation_directory_exists=self._detect_install_directory(),
            desktop_file_exists=self._detect_desktop_file(),
            version=self._read_version(),
        )

    def install(self) -> None:
        """Install Cursor from a local .deb package."""

        LOGGER.info("Starting Cursor installation")
        previous_state = deepcopy(self.state_manager.load())
        self.validate_input()
        self.detect_existing_installation()
        self.verify_dependencies()
        self.verify_package()
        try:
            self.install_package()
            self.verify_installation()
            self.update_state()
        except Exception:
            LOGGER.exception("Cursor installation failed; rolling back state")
            self.rollback(previous_state)
            raise
        LOGGER.info("Cursor installation completed")

    def update(self) -> str:
        """Placeholder update flow that reports the current version."""

        version = self.detect().version or "unknown"
        message = f"Cursor update is not implemented yet. Current version: {version}"
        LOGGER.info(message)
        return message

    def uninstall(self) -> None:
        """Remove Cursor using apt and update local state."""

        LOGGER.info("Uninstalling Cursor")
        self.remove_package()
        self.remove_desktop_entry()
        self.remove_state()
        LOGGER.info("Cursor uninstalled")

    def doctor(self) -> CursorDoctorReport:
        """Return structured diagnostics for Cursor."""

        detection = self.detect()
        state = self.state_manager.load()
        applications = state.get("applications", [])
        recorded = next(
            (item for item in applications if item.get("name") == DEFAULT_PACKAGE_NAME),
            None,
        )
        filesystem_matches = bool(recorded) and detection.executable_exists
        diagnostics = CursorDoctorReport(
            name=DEFAULT_PACKAGE_NAME,
            executable_exists=detection.executable_exists,
            desktop_launcher_exists=detection.desktop_file_exists,
            version_available=detection.version is not None,
            state_matches_filesystem=filesystem_matches,
            recorded_state=recorded,
        )
        LOGGER.info("Cursor diagnostics collected")
        return diagnostics

    def validate_input(self) -> None:
        """Validate local installer inputs."""

        LOGGER.info("Validating Cursor package input")
        architecture = self._detect_architecture()
        if architecture not in {"amd64", "arm64"}:
            raise RuntimeError(f"Unsupported architecture: {architecture}")
        if not self.package_path.is_file():
            raise FileNotFoundError(f"Cursor package not found: {self.package_path}")

    def detect_existing_installation(self) -> CursorDetection:
        """Detect an already installed Cursor instance."""

        detection = self.detect()
        LOGGER.info("Detected existing installation: %s", detection.installed)
        return detection

    def verify_dependencies(self) -> None:
        """Verify required system dependencies."""

        LOGGER.info("Verifying Cursor dependencies")
        status = self.dependency_manager.detect()
        if not status.apt:
            raise RuntimeError("apt is required for Cursor installation")
        if not status.sudo:
            raise RuntimeError("sudo is required for Cursor installation")

    def verify_package(self) -> None:
        """Verify that the package is ready for installation."""

        LOGGER.info("Verifying Cursor package availability")
        if not self.package_path.exists():
            raise FileNotFoundError(f"Cursor package not found: {self.package_path}")

    def install_package(self) -> None:
        """Install the .deb package via apt."""

        LOGGER.info("Installing Cursor package from %s", self.package_path)
        run_sudo(["apt", "install", "-y", str(self.package_path)], check=True)

    def verify_installation(self) -> CursorDetection:
        """Ensure the installation produced a usable executable."""

        detection = self.detect()
        if not detection.executable_exists:
            raise RuntimeError("Cursor installation did not produce an executable")
        LOGGER.info("Verified Cursor installation")
        return detection

    def update_state(self) -> None:
        """Persist the installed Cursor state."""

        detection = self.detect()
        self._record_state(detection)
        LOGGER.info("Recorded Cursor state")

    def rollback(self, previous_state: dict[str, Any]) -> None:
        """Restore the prior state after installation failure."""

        LOGGER.info("Restoring previous Cursor state")
        self.state_manager.state = previous_state
        self.state_manager.save()

    def remove_package(self) -> None:
        """Remove the package using apt."""

        if command_exists("apt"):
            run_sudo(["apt", "remove", "-y", DEFAULT_PACKAGE_NAME], check=True)
            run_sudo(["apt", "autoremove", "-y"], check=False)

    def remove_desktop_entry(self) -> None:
        """Remove the desktop launcher if present."""

        if self.desktop_file.exists():
            remove_path(self.desktop_file)

    def remove_state(self) -> None:
        """Remove Cursor from the recorded state."""

        self.state_manager.load()
        self.state_manager.remove_application(DEFAULT_PACKAGE_NAME)

    def _record_state(self, detection: CursorDetection) -> None:
        record = CursorInstallationRecord(version=detection.version)
        self.state_manager.load()
        self.state_manager.state["applications"] = [
            item
            for item in self.state_manager.list_installed()
            if item.get("name") != DEFAULT_PACKAGE_NAME
        ]
        self.state_manager.record_application(record.__dict__)

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
