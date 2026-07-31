"""Devin installer implementation."""

from __future__ import annotations

import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiws.shell import command_exists, run

from .base import BaseInstaller

DEFAULT_DEVIN_ARCHIVE = Path("/tmp/devin.tar.gz")
DEFAULT_INSTALL_DIR = Path("~/.local/share/aiws/apps/Devin").expanduser()
DEFAULT_EXECUTABLE = Path("~/.local/bin/devin").expanduser()
DEFAULT_DESKTOP_FILE = Path("~/.local/share/applications/devin.desktop").expanduser()
DEFAULT_PACKAGE_NAME = "devin"


@dataclass(frozen=True)
class DevinDetection:
    """Structured detection data for Devin."""

    executable_exists: bool
    installation_directory_exists: bool
    desktop_file_exists: bool
    version: str | None

    @property
    def installed(self) -> bool:
        return self.executable_exists or self.installation_directory_exists


@dataclass(frozen=True)
class DevinInstallationRecord:
    """Persisted Devin installation details."""

    name: str = "Devin"
    install_path: str = str(DEFAULT_INSTALL_DIR)
    executable: str = str(DEFAULT_EXECUTABLE)
    version: str | None = None
    installation_type: str = "tar.gz"


@dataclass(frozen=True)
class DevinDoctorReport:
    """Structured diagnostics for Devin."""

    name: str
    executable_exists: bool
    desktop_launcher_exists: bool
    version_available: bool
    state_matches_filesystem: bool
    recorded_state: dict[str, Any] | None


@dataclass
class DevinInstaller(BaseInstaller):
    """Installer for the Devin IDE."""

    package_path: Path = DEFAULT_DEVIN_ARCHIVE
    executable_path: Path = DEFAULT_EXECUTABLE
    desktop_file: Path = DEFAULT_DESKTOP_FILE
    install_dir: Path = DEFAULT_INSTALL_DIR
    name: str = "Devin"
    binary_name: str = "devin"

    def detect(self) -> DevinDetection:
        return DevinDetection(
            executable_exists=self._detect_executable(),
            installation_directory_exists=self._detect_install_directory(),
            desktop_file_exists=self._detect_desktop_file(),
            version=self._read_version(),
        )

    def update(self) -> str:
        version = self.detect().version or "unknown"
        message = f"Devin update is not implemented yet. Current version: {version}"
        self.logger.info(message)
        return message

    def doctor(self) -> DevinDoctorReport:
        detection = self.detect()
        state = self.state_manager.load()
        applications = state.get("applications", [])
        recorded = next(
            (item for item in applications if item.get("name") == self.name),
            None,
        )
        diagnostics = DevinDoctorReport(
            name=self.name,
            executable_exists=detection.executable_exists,
            desktop_launcher_exists=detection.desktop_file_exists,
            version_available=detection.version is not None,
            state_matches_filesystem=bool(recorded) and detection.executable_exists,
            recorded_state=recorded,
        )
        self.logger.info("Devin diagnostics collected")
        return diagnostics

    def install_package(self) -> None:
        self.logger.info("Extracting Devin archive from %s", self.package_path)
        self.install_dir.parent.mkdir(parents=True, exist_ok=True)
        self.install_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(self.package_path, "r:gz") as archive:
            archive.extractall(self.install_dir)
        self._ensure_binary_layout()

    def create_desktop_launcher(self) -> None:
        if self.desktop_file.exists():
            return
        self.desktop_file.parent.mkdir(parents=True, exist_ok=True)
        self.desktop_file.write_text(self.desktop_launcher_contents(), encoding="utf-8")

    def desktop_launcher_contents(self) -> str:
        icon_line = (
            f"Icon={self._desktop_icon_path()}\n" if self._desktop_icon_path() else ""
        )
        return (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={self.name}\n"
            f"Exec={self.executable_path}\n"
            f"{icon_line}"
        )

    def symlink_target(self) -> Path:
        return self.install_dir / self.binary_name

    def package_name(self) -> str:
        return self.name

    def _record_state(self, detection: DevinDetection) -> None:
        record = DevinInstallationRecord(version=detection.version)
        self.state_manager.load()
        self.state_manager.state["applications"] = [
            item
            for item in self.state_manager.list_installed()
            if item.get("name") != self.name
        ]
        self.state_manager.record_application(record.__dict__)

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

    def _ensure_binary_layout(self) -> None:
        source = self._find_extracted_binary()
        if source is None:
            raise FileNotFoundError("Devin binary not found in extracted archive")
        target = self.install_dir / self.binary_name
        if target.exists():
            return
        target.symlink_to(source)

    def _find_extracted_binary(self) -> Path | None:
        candidates = [
            path
            for path in self.install_dir.rglob(self.binary_name)
            if path.is_file() and path.name == self.binary_name
        ]
        return candidates[0] if candidates else None

    def _desktop_icon_path(self) -> str | None:
        for pattern in ("*.png", "*.svg", "*.xpm"):
            for icon_path in self.install_dir.rglob(pattern):
                if icon_path.is_file():
                    return str(icon_path)
        return None

    @staticmethod
    def _extract_version(output: str) -> str | None:
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
        return match.group(1) if match else output.strip() or None
