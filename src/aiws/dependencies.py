"""Dependency detection and preparation."""

from __future__ import annotations

import shutil
import socket
import sys
from dataclasses import dataclass
from pathlib import Path

from .shell import command_exists


@dataclass(frozen=True)
class DependencyStatus:
    python: bool
    git: bool
    sudo: bool
    internet: bool
    disk_space_ok: bool
    apt: bool


@dataclass
class DependencyManager:
    """Detect platform prerequisites."""

    minimum_free_bytes: int = 5 * 1024 * 1024 * 1024

    def detect_python(self) -> bool:
        return sys.version_info >= (3, 12)

    def detect_git(self) -> bool:
        return command_exists("git")

    def detect_sudo(self) -> bool:
        return command_exists("sudo")

    def detect_internet(self) -> bool:
        try:
            with socket.create_connection(("1.1.1.1", 53), timeout=2):
                return True
        except OSError:
            return False

    def detect_disk_space(self, path: Path | None = None) -> bool:
        target = path or Path.home()
        usage = shutil.disk_usage(target)
        return usage.free >= self.minimum_free_bytes

    def detect_apt(self) -> bool:
        return command_exists("apt")

    def detect(self) -> DependencyStatus:
        return DependencyStatus(
            python=self.detect_python(),
            git=self.detect_git(),
            sudo=self.detect_sudo(),
            internet=self.detect_internet(),
            disk_space_ok=self.detect_disk_space(),
            apt=self.detect_apt(),
        )

    def prepare(self, dry_run: bool = False) -> DependencyStatus:
        status = self.detect()
        if dry_run:
            return status
        return status
