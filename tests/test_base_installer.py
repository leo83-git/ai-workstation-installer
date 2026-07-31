from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.tools.base import BaseInstaller


class _DemoInstaller(BaseInstaller):
    def detect(self) -> bool:
        return True

    def update(self) -> None:
        return None

    def doctor(self) -> list[str]:
        return []

    def install_package(self) -> None:
        return None

    def _record_state(self, detection: bool) -> None:
        return None


class BaseInstallerBackupTests(unittest.TestCase):
    def _installer(self, tmp_path: Path) -> _DemoInstaller:
        package = tmp_path / "package.bin"
        package.write_text("pkg", encoding="utf-8")
        return _DemoInstaller(
            name="demo",
            package_path=package,
            executable_path=tmp_path / "bin/demo",
            desktop_file=tmp_path / "share/applications/demo.desktop",
            install_dir=tmp_path / "opt/demo",
        )

    def test_successful_installation_commits_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(installer, "commit_backup") as commit_mock,
            ):
                installer.install()

            commit_mock.assert_called_once()

    def test_helper_methods_delegate_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.desktop_manager, "install_entry"
                ) as install_mock,
                patch.object(installer.desktop_manager, "remove_entry") as remove_mock,
            ):
                installer.create_desktop_launcher()
                installer.remove_desktop_entry()

            install_mock.assert_called_once()
            remove_mock.assert_called_once()

    def test_failed_installation_restores_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(
                    installer,
                    "install_package",
                    side_effect=RuntimeError("boom"),
                ),
                patch.object(installer, "restore_backup") as restore_mock,
            ):
                with self.assertRaises(RuntimeError):
                    installer.install()

            restore_mock.assert_called_once()

    def test_original_exception_is_reraised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(
                    installer,
                    "install_package",
                    side_effect=RuntimeError("original"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "original"):
                    installer.install()

    def test_rollback_failures_are_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(
                    installer,
                    "install_package",
                    side_effect=RuntimeError("boom"),
                ),
                patch.object(
                    installer,
                    "restore_backup",
                    side_effect=RuntimeError("restore failed"),
                ),
                patch.object(
                    installer,
                    "rollback",
                    side_effect=RuntimeError("state rollback failed"),
                ),
            ):
                with self.assertLogs("test_base_installer", level="ERROR") as logs:
                    with self.assertRaisesRegex(RuntimeError, "boom"):
                        installer.install()

            self.assertTrue(
                any(
                    "Rollback failed while restoring backups" in entry
                    for entry in logs.output
                )
            )

    def test_desktop_integration_failures_do_not_fail_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installer = self._installer(Path(tmp))
            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(
                    installer.desktop_manager,
                    "install_entry",
                    side_effect=RuntimeError("desktop failed"),
                ),
            ):
                installer.install()
