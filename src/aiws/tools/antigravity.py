"""Antigravity installer implementation."""

from __future__ import annotations

import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiws.shell import command_exists, run

from .base import BaseInstaller

DEFAULT_ANTIGRAVITY_ARCHIVE = Path("/tmp/antigravity.tar.gz")
DEFAULT_INSTALL_DIR = Path("~/.local/share/aiws/apps/Antigravity").expanduser()
DEFAULT_EXECUTABLE = Path("~/.local/bin/antigravity").expanduser()
DEFAULT_DESKTOP_FILE = Path(
    "~/.local/share/applications/antigravity.desktop"
).expanduser()
DEFAULT_PACKAGE_NAME = "antigravity"


@dataclass(frozen=True)
class AntigravityDetection:
    """Structured detection data for Antigravity."""

    executable_exists: bool
    installation_directory_exists: bool
    desktop_file_exists: bool
    version: str | None

    @property
    def installed(self) -> bool:
        return self.executable_exists or self.installation_directory_exists


@dataclass(frozen=True)
class AntigravityInstallationRecord:
    """Persisted Antigravity installation details."""

    name: str = "Antigravity"
    install_path: str = str(DEFAULT_INSTALL_DIR)
    executable: str = str(DEFAULT_EXECUTABLE)
    version: str | None = None
    installation_type: str = "tar.gz"


@dataclass(frozen=True)
class AntigravityDoctorReport:
    """Structured diagnostics for Antigravity."""

    name: str
    executable_exists: bool
    desktop_launcher_exists: bool
    version_available: bool
    state_matches_filesystem: bool
    recorded_state: dict[str, Any] | None


@dataclass
class AntigravityInstaller(BaseInstaller):
    """Installer for the Antigravity IDE."""

    package_path: Path = DEFAULT_ANTIGRAVITY_ARCHIVE
    executable_path: Path = DEFAULT_EXECUTABLE
    desktop_file: Path = DEFAULT_DESKTOP_FILE
    install_dir: Path = DEFAULT_INSTALL_DIR
    name: str = "Antigravity"
    binary_name: str = "antigravity"

    def detect(self) -> AntigravityDetection:
        return AntigravityDetection(
            executable_exists=self._detect_executable(),
            installation_directory_exists=self._detect_install_directory(),
            desktop_file_exists=self._detect_desktop_file(),
            version=self._read_version(),
        )

    def update(self) -> str:
        version = self.detect().version or "unknown"
        message = (
            f"Antigravity update is not implemented yet. Current version: {version}"
        )
        self.logger.info(message)
        return message

    def doctor(self) -> AntigravityDoctorReport:
        detection = self.detect()
        state = self.state_manager.load()
        applications = state.get("applications", [])
        recorded = next(
            (item for item in applications if item.get("name") == self.name),
            None,
        )
        diagnostics = AntigravityDoctorReport(
            name=self.name,
            executable_exists=detection.executable_exists,
            desktop_launcher_exists=detection.desktop_file_exists,
            version_available=detection.version is not None,
            state_matches_filesystem=bool(recorded) and detection.executable_exists,
            recorded_state=recorded,
        )
        self.logger.info("Antigravity diagnostics collected")
        return diagnostics

    def verify_installation(self) -> AntigravityDetection:
        detection = self.detect()
        if not detection.executable_exists or detection.version is None:
            raise RuntimeError(
                "Antigravity installation did not produce a versioned executable"
            )
        self.logger.info("Verified Antigravity installation")
        return detection

    def install_package(self) -> None:
        self.logger.info("Extracting Antigravity archive from %s", self.package_path)
        self.install_dir.parent.mkdir(parents=True, exist_ok=True)
        self.install_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(self.package_path, "r:gz") as archive:
            archive.extractall(self.install_dir)
        self._ensure_binary_layout()

    def symlink_target(self) -> Path:
        return self.install_dir / self.binary_name

    def package_name(self) -> str:
        return self.name

    def _record_state(self, detection: AntigravityDetection) -> None:
        record = AntigravityInstallationRecord(version=detection.version)
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

    def desktop_entry_icon_path(self) -> Path | None:
        return self._desktop_icon_path()

    def desktop_entry_requires_icon(self) -> bool:
        return True

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
            raise FileNotFoundError("Antigravity binary not found in extracted archive")
        target = self.install_dir / self.binary_name
        if target.exists() or target.is_symlink():
            return
        target.symlink_to(source)

    def _find_extracted_binary(self) -> Path | None:
        candidates = [
            path
            for path in self.install_dir.rglob(self.binary_name)
            if path.is_file() and path.name == self.binary_name
        ]
        return candidates[0] if candidates else None

    def _desktop_icon_path(self) -> Path | None:
        for pattern in ("*.png", "*.svg", "*.xpm"):
            for icon_path in self.install_dir.rglob(pattern):
                if icon_path.is_file():
                    return icon_path
        return None

    @staticmethod
    def _extract_version(output: str) -> str | None:
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
        return match.group(1) if match else output.strip() or None
