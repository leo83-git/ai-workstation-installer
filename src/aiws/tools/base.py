"""Tool installer base classes."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiws.backup import BackupManager
from aiws.dependencies import DependencyManager
from aiws.filesystem import remove_path
from aiws.shell import command_exists, run_sudo
from aiws.state import StateManager


class ToolInstaller(ABC):
    """Abstract tool installer interface."""

    @abstractmethod
    def detect(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def install(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def uninstall(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def doctor(self) -> Any:
        raise NotImplementedError


@dataclass
class BaseInstaller(ToolInstaller):
    """Shared installer lifecycle and system helpers."""

    name: str
    package_path: Path
    executable_path: Path
    desktop_file: Path
    install_dir: Path
    sha256_checksum: str | None = None
    backup_manager: BackupManager = field(default_factory=BackupManager)
    dependency_manager: DependencyManager = field(default_factory=DependencyManager)
    state_manager: StateManager = field(default_factory=StateManager)
    logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__module__)

    def install(self) -> None:
        self.logger.info("Starting %s installation", self.name)
        previous_state = deepcopy(self.state_manager.load())
        self.validate_input()
        self.detect_existing_installation()
        self.verify_dependencies()
        self.verify_package()
        self.begin_backup()
        try:
            self.install_package()
            self.create_desktop_launcher()
            self.create_symlink()
            self.verify_installation()
            self.update_state()
            self.commit_backup()
        except Exception:
            self.logger.exception(
                "%s installation failed; rolling back state", self.name
            )
            try:
                self.restore_backup()
            except Exception:
                self.logger.exception("Rollback failed while restoring backups")
            try:
                self.rollback(previous_state)
            except Exception:
                self.logger.exception("Rollback failed while restoring state")
            raise
        self.logger.info("%s installation completed", self.name)

    def uninstall(self) -> None:
        self.logger.info("Uninstalling %s", self.name)
        self.remove_package()
        self.remove_desktop_entry()
        self.remove_symlink()
        self.remove_state()
        self.logger.info("%s uninstalled", self.name)

    def validate_input(self) -> None:
        self.logger.info("Validating %s installer input", self.name)
        if not self.package_path:
            raise RuntimeError("package_path is required")

    def detect_existing_installation(self) -> Any:
        detection = self.detect()
        self.logger.info(
            "Detected existing installation: %s", self._installed_flag(detection)
        )
        return detection

    def verify_dependencies(self) -> None:
        self.logger.info("Verifying %s dependencies", self.name)
        status = self.dependency_manager.detect()
        if not status.apt:
            raise RuntimeError("apt is required")
        if not status.sudo:
            raise RuntimeError("sudo is required")

    def verify_package(self) -> None:
        self.logger.info("Verifying %s package availability", self.name)
        if not self.package_path.exists():
            raise FileNotFoundError(
                f"{self.name} package not found: {self.package_path}"
            )

    def verify_installation(self) -> Any:
        detection = self.detect()
        if not self._installed_flag(detection):
            raise RuntimeError(
                f"{self.name} installation did not produce a usable install"
            )
        self.logger.info("Verified %s installation", self.name)
        return detection

    def update_state(self) -> None:
        self.logger.info("Recording %s state", self.name)
        self._record_state(self.detect())

    def rollback(self, previous_state: dict[str, Any]) -> None:
        self.logger.info("Restoring previous %s state", self.name)
        self.state_manager.state = previous_state
        self.state_manager.save()

    def create_desktop_launcher(self) -> None:
        self.backup_file(self.desktop_file)
        if self.desktop_file.exists():
            return
        self.desktop_file.parent.mkdir(parents=True, exist_ok=True)
        self.desktop_file.write_text(self.desktop_launcher_contents(), encoding="utf-8")

    def create_symlink(self) -> None:
        self.backup_file(self.executable_path)
        if self.executable_path.exists():
            return
        self.executable_path.parent.mkdir(parents=True, exist_ok=True)
        self.executable_path.symlink_to(self.symlink_target())

    def remove_package(self) -> None:
        if command_exists("apt"):
            run_sudo(["apt", "remove", "-y", self.package_name()], check=True)
            run_sudo(["apt", "autoremove", "-y"], check=False)

    def remove_desktop_entry(self) -> None:
        if self.desktop_file.exists():
            remove_path(self.desktop_file)

    def remove_symlink(self) -> None:
        if self.executable_path.exists() or self.executable_path.is_symlink():
            remove_path(self.executable_path)

    def remove_state(self) -> None:
        self.state_manager.load()
        self.state_manager.remove_application(self.package_name())

    def package_name(self) -> str:
        return self.name

    def desktop_launcher_contents(self) -> str:
        return (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={self.name}\n"
            f"Exec={self.executable_path}\n"
        )

    def symlink_target(self) -> Path:
        return self.install_dir / self.name

    def _installed_flag(self, detection: Any) -> bool:
        return bool(detection)

    def begin_backup(self) -> None:
        self.backup_manager.begin()

    def backup_file(self, path: Path) -> Path | None:
        return self.backup_manager.backup_file(path)

    def restore_backup(self) -> None:
        self.backup_manager.restore()

    def commit_backup(self) -> None:
        self.backup_manager.commit()

    @abstractmethod
    def install_package(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _record_state(self, detection: Any) -> None:
        raise NotImplementedError
