"""Backup and rollback helpers."""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

LOGGER = logging.getLogger(__name__)


@dataclass
class BackupManager:
    """Track file backups for a single installation transaction."""

    workspace: Path | None = None
    _entries: dict[Path, Path] = field(default_factory=dict, init=False, repr=False)
    _started: bool = field(default=False, init=False, repr=False)
    _committed: bool = field(default=False, init=False, repr=False)

    def begin(self) -> None:
        if self._started and self.workspace is not None:
            return
        self.workspace = self.workspace or Path(tempfile.mkdtemp(prefix="aiws-backup-"))
        self._started = True
        self._committed = False
        LOGGER.info("Backup started in %s", self.workspace)

    def backup_file(self, path: Path) -> Path | None:
        self.begin()
        if not path.exists():
            return None
        backup_path = self._backup_path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        self._entries[path] = backup_path
        LOGGER.info("File backed up: %s", path)
        return backup_path

    def restore(self) -> None:
        self.begin()
        LOGGER.info("Rollback started")
        for original, backup in list(self._entries.items()):
            try:
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, original)
                LOGGER.info("File restored: %s", original)
            except Exception:
                LOGGER.exception("Rollback failed for %s", original)

    def commit(self) -> None:
        if self.workspace is None or self._committed:
            return
        shutil.rmtree(self.workspace, ignore_errors=True)
        self._entries.clear()
        self._committed = True
        LOGGER.info("Temporary backups removed")

    def _backup_path(self, path: Path) -> Path:
        assert self.workspace is not None
        return self.workspace / path.as_posix().lstrip("/")


def create_backup_plan() -> dict[str, str]:
    """Return a compatibility placeholder for older callers."""

    return {"status": "placeholder"}
