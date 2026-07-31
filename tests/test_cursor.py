from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.state import StateManager
from aiws.tools.cursor import (
    DEFAULT_INSTALL_DIR,
    CursorDetection,
    CursorDoctorReport,
    CursorInstaller,
)


class CursorInstallerTests(unittest.TestCase):
    def test_detect_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "cursor"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            install_dir = tmp_path / "Cursor"
            install_dir.mkdir()
            desktop_file = tmp_path / "cursor.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")

            installer = CursorInstaller(
                executable_path=executable,
                install_dir=install_dir,
                desktop_file=desktop_file,
            )

            with (
                patch("aiws.tools.cursor.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                detection = installer.detect()

            self.assertIsInstance(detection, CursorDetection)
            self.assertTrue(detection.executable_exists)
            self.assertTrue(detection.installation_directory_exists)
            self.assertTrue(detection.desktop_file_exists)
            self.assertEqual(detection.version, "1.2.3")

    def test_install_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package = tmp_path / "cursor.deb"
            package.write_text("deb", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            executable = tmp_path / "usr/bin/cursor"
            desktop_file = tmp_path / "usr/share/applications/cursor.desktop"
            install_dir = tmp_path / "opt/Cursor"
            installer = CursorInstaller(
                package_path=package,
                state_manager=state_manager,
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=install_dir,
            )

            with (
                patch.object(installer, "_detect_architecture", return_value="amd64"),
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(installer, "install_package"),
                patch.object(
                    installer,
                    "detect",
                    return_value=CursorDetection(True, True, True, "1.2.3"),
                ),
            ):
                installer.install()

            stored = installer.state_manager.load()["applications"]
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["name"], "cursor")
            self.assertEqual(stored[0]["version"], "1.2.3")

    def test_install_failure_restores_previous_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package = tmp_path / "cursor.deb"
            package.write_text("deb", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.state["applications"] = [{"name": "existing"}]
            state_manager.save()
            executable = tmp_path / "usr/bin/cursor"
            desktop_file = tmp_path / "usr/share/applications/cursor.desktop"
            install_dir = tmp_path / "opt/Cursor"
            installer = CursorInstaller(
                package_path=package,
                state_manager=state_manager,
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=install_dir,
            )

            with (
                patch.object(installer, "_detect_architecture", return_value="amd64"),
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
            ):
                with self.assertRaises(RuntimeError):
                    installer.install()

            restored = installer.state_manager.load()["applications"]
            self.assertEqual(restored, [{"name": "existing"}])

    def test_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            desktop_file = tmp_path / "cursor.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.state["applications"] = [{"name": "cursor"}]
            state_manager.save()
            installer = CursorInstaller(
                state_manager=state_manager,
                desktop_file=desktop_file,
                executable_path=tmp_path / "usr/bin/cursor",
                install_dir=tmp_path / "opt/Cursor",
            )

            with (
                patch("aiws.tools.base.command_exists", return_value=True),
                patch("aiws.tools.base.run_sudo") as run_sudo_mock,
                patch("aiws.tools.base.remove_path") as remove_path_mock,
            ):
                installer.uninstall()

            self.assertEqual(installer.state_manager.load()["applications"], [])
            run_sudo_mock.assert_any_call(["apt", "remove", "-y", "cursor"], check=True)
            remove_path_mock.assert_called_once_with(desktop_file)

    def test_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "cursor"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            desktop_file = tmp_path / "cursor.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.record_application(
                {
                    "name": "cursor",
                    "version": "1.2.3",
                    "install_path": str(DEFAULT_INSTALL_DIR),
                    "executable": str(executable),
                    "installation_type": "deb",
                }
            )
            installer = CursorInstaller(
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=tmp_path / "opt/Cursor",
                state_manager=state_manager,
            )

            with (
                patch("aiws.tools.cursor.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                report = installer.doctor()

            self.assertIsInstance(report, CursorDoctorReport)
            self.assertTrue(report.executable_exists)
            self.assertTrue(report.desktop_launcher_exists)
            self.assertTrue(report.version_available)
            self.assertTrue(report.state_matches_filesystem)
            self.assertEqual(report.recorded_state["version"], "1.2.3")
