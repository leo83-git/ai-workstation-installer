from __future__ import annotations

import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.state import StateManager
from aiws.tools.devin import (
    DEFAULT_INSTALL_DIR,
    DevinDetection,
    DevinDoctorReport,
    DevinInstaller,
)


class DevinInstallerTests(unittest.TestCase):
    def _create_archive(self, archive_path: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app_dir = tmp_path / "Devin"
            app_dir.mkdir()
            binary = app_dir / "devin"
            binary.write_text("#!/bin/sh\n", encoding="utf-8")
            icon = app_dir / "icon.png"
            icon.write_text("icon", encoding="utf-8")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(binary, arcname="Devin/devin")
                archive.add(icon, arcname="Devin/icon.png")

    def test_detect_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "devin"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            install_dir = tmp_path / "Devin"
            install_dir.mkdir()
            desktop_file = tmp_path / "devin.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")

            installer = DevinInstaller(
                executable_path=executable,
                install_dir=install_dir,
                desktop_file=desktop_file,
            )

            with (
                patch("aiws.tools.devin.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                detection = installer.detect()

            self.assertIsInstance(detection, DevinDetection)
            self.assertTrue(detection.executable_exists)
            self.assertTrue(detection.installation_directory_exists)
            self.assertTrue(detection.desktop_file_exists)
            self.assertEqual(detection.version, "1.2.3")

    def test_install_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            package = tmp_path / "devin.tar.gz"
            self._create_archive(package)
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            executable = tmp_path / "bin/devin"
            desktop_file = tmp_path / "share/applications/devin.desktop"
            install_dir = tmp_path / "apps/Devin"
            installer = DevinInstaller(
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
                    return_value=DevinDetection(True, True, True, "1.2.3"),
                ),
            ):
                installer.install()

            stored = installer.state_manager.load()["applications"]
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["name"], "Devin")
            self.assertEqual(stored[0]["version"], "1.2.3")
            self.assertTrue(desktop_file.exists())
            self.assertTrue(executable.is_symlink())

    def test_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            desktop_file = tmp_path / "devin.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            executable = tmp_path / "bin/devin"
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.symlink_to(tmp_path / "apps/Devin/devin")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.state["applications"] = [{"name": "Devin"}]
            state_manager.save()
            installer = DevinInstaller(
                state_manager=state_manager,
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=tmp_path / "apps/Devin",
            )

            with (
                patch("aiws.tools.base.command_exists", return_value=True),
                patch("aiws.tools.base.run_sudo") as run_sudo_mock,
                patch.object(installer.desktop_manager, "remove_entry") as remove_mock,
            ):
                installer.uninstall()

            self.assertEqual(installer.state_manager.load()["applications"], [])
            run_sudo_mock.assert_any_call(["apt", "remove", "-y", "Devin"], check=True)
            remove_mock.assert_called_once_with(desktop_file, icon_name="Devin")

    def test_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            executable = tmp_path / "devin"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            desktop_file = tmp_path / "devin.desktop"
            desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
            state_path = tmp_path / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.record_application(
                {
                    "name": "Devin",
                    "version": "1.2.3",
                    "install_path": str(DEFAULT_INSTALL_DIR),
                    "executable": str(executable),
                    "installation_type": "tar.gz",
                }
            )
            installer = DevinInstaller(
                executable_path=executable,
                desktop_file=desktop_file,
                install_dir=tmp_path / "apps/Devin",
                state_manager=state_manager,
            )

            with (
                patch("aiws.tools.devin.command_exists", return_value=True),
                patch.object(installer, "_read_version", return_value="1.2.3"),
            ):
                report = installer.doctor()

            self.assertIsInstance(report, DevinDoctorReport)
            self.assertTrue(report.executable_exists)
            self.assertTrue(report.desktop_launcher_exists)
            self.assertTrue(report.version_available)
            self.assertTrue(report.state_matches_filesystem)
            self.assertEqual(report.recorded_state["version"], "1.2.3")
