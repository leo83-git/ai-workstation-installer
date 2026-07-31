from __future__ import annotations

import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.state import StateManager
from aiws.tools.antigravity import (
    DEFAULT_INSTALL_DIR,
    AntigravityDetection,
    AntigravityDoctorReport,
    AntigravityInstaller,
)


class AntigravityInstallerTests(unittest.TestCase):
    def _create_archive(self, archive_path: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app_dir = tmp_path / "Antigravity"
            app_dir.mkdir()
            binary = app_dir / "antigravity"
            binary.write_text("#!/bin/sh\n", encoding="utf-8")
            icon = app_dir / "icon.png"
            icon.write_text("icon", encoding="utf-8")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(binary, arcname="Antigravity/antigravity")
                archive.add(icon, arcname="Antigravity/icon.png")

    def test_detect_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "antigravity"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            install_dir = tmp_path / "Antigravity"
            install_dir.mkdir()
            desktop_file = tmp_path / "antigravity.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")

            installer = AntigravityInstaller(
                executable_path=executable,
                install_dir=install_dir,
                desktop_file=desktop_file,
            )

            with (
                patch("aiws.tools.antigravity.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                detection = installer.detect()

            self.assertIsInstance(detection, AntigravityDetection)
            self.assertTrue(detection.executable_exists)
            self.assertTrue(detection.installation_directory_exists)
            self.assertTrue(detection.desktop_file_exists)
            self.assertEqual(detection.version, "1.2.3")

    def test_install_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package = tmp_path / "antigravity.tar.gz"
            self._create_archive(package)
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            executable = tmp_path / "bin/antigravity"
            desktop_file = tmp_path / "share/applications/antigravity.desktop"
            install_dir = tmp_path / "apps/Antigravity"
            installer = AntigravityInstaller(
                package_path=package,
                state_manager=state_manager,
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=install_dir,
            )

            with (
                patch.object(
                    installer.dependency_manager,
                    "detect",
                    return_value=type("Status", (), {"apt": True, "sudo": True})(),
                ),
                patch.object(
                    installer,
                    "detect",
                    return_value=AntigravityDetection(True, True, True, "1.2.3"),
                ),
            ):
                installer.install()

            stored = installer.state_manager.load()["applications"]
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["name"], "Antigravity")
            self.assertEqual(stored[0]["version"], "1.2.3")
            self.assertTrue(desktop_file.exists())
            self.assertTrue(executable.is_symlink())

    def test_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            desktop_file = tmp_path / "antigravity.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            executable = tmp_path / "bin/antigravity"
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.symlink_to(tmp_path / "apps/Antigravity/antigravity")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.state["applications"] = [{"name": "Antigravity"}]
            state_manager.save()
            installer = AntigravityInstaller(
                state_manager=state_manager,
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=tmp_path / "apps/Antigravity",
            )

            with (
                patch("aiws.tools.base.command_exists", return_value=True),
                patch("aiws.tools.base.run_sudo") as run_sudo_mock,
                patch("aiws.tools.base.remove_path") as remove_path_mock,
            ):
                installer.uninstall()

            self.assertEqual(installer.state_manager.load()["applications"], [])
            run_sudo_mock.assert_any_call(
                ["apt", "remove", "-y", "Antigravity"], check=True
            )
            remove_path_mock.assert_any_call(desktop_file)
            remove_path_mock.assert_any_call(executable)

    def test_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "antigravity"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            desktop_file = tmp_path / "antigravity.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.record_application(
                {
                    "name": "Antigravity",
                    "version": "1.2.3",
                    "install_path": str(DEFAULT_INSTALL_DIR),
                    "executable": str(executable),
                    "installation_type": "tar.gz",
                }
            )
            installer = AntigravityInstaller(
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=tmp_path / "apps/Antigravity",
                state_manager=state_manager,
            )

            with (
                patch("aiws.tools.antigravity.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                report = installer.doctor()

            self.assertIsInstance(report, AntigravityDoctorReport)
            self.assertTrue(report.executable_exists)
            self.assertTrue(report.desktop_launcher_exists)
            self.assertTrue(report.version_available)
            self.assertTrue(report.state_matches_filesystem)
            self.assertEqual(report.recorded_state["version"], "1.2.3")
