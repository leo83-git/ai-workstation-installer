from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiws.backup import BackupManager


class BackupManagerTests(unittest.TestCase):
    def test_backup_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.txt"
            source.write_text("hello", encoding="utf-8")

            manager = BackupManager(workspace=tmp_path / "backups")
            backup_path = manager.backup_file(source)

            self.assertIsNotNone(backup_path)
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "hello")

    def test_backup_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "missing.txt"

            manager = BackupManager(workspace=tmp_path / "backups")
            backup_path = manager.backup_file(source)

            self.assertIsNone(backup_path)

    def test_restore_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.txt"
            source.write_text("original", encoding="utf-8")
            manager = BackupManager(workspace=tmp_path / "backups")
            manager.backup_file(source)
            source.write_text("changed", encoding="utf-8")

            manager.restore()

            self.assertEqual(source.read_text(encoding="utf-8"), "original")

    def test_restore_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            first = tmp_path / "first.txt"
            second = tmp_path / "nested" / "second.txt"
            first.write_text("one", encoding="utf-8")
            second.parent.mkdir(parents=True, exist_ok=True)
            second.write_text("two", encoding="utf-8")
            manager = BackupManager(workspace=tmp_path / "backups")
            manager.backup_file(first)
            manager.backup_file(second)
            first.write_text("changed-one", encoding="utf-8")
            second.write_text("changed-two", encoding="utf-8")

            manager.restore()

            self.assertEqual(first.read_text(encoding="utf-8"), "one")
            self.assertEqual(second.read_text(encoding="utf-8"), "two")

    def test_commit_removes_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.txt"
            source.write_text("hello", encoding="utf-8")
            manager = BackupManager(workspace=tmp_path / "backups")
            manager.backup_file(source)

            manager.commit()

            self.assertFalse((tmp_path / "backups").exists())

    def test_repeated_commit_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.txt"
            source.write_text("hello", encoding="utf-8")
            manager = BackupManager(workspace=tmp_path / "backups")
            manager.backup_file(source)

            manager.commit()
            manager.commit()

            self.assertFalse((tmp_path / "backups").exists())

    def test_repeated_restore_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.txt"
            source.write_text("original", encoding="utf-8")
            manager = BackupManager(workspace=tmp_path / "backups")
            manager.backup_file(source)
            source.write_text("changed", encoding="utf-8")

            manager.restore()
            manager.restore()

            self.assertEqual(source.read_text(encoding="utf-8"), "original")
