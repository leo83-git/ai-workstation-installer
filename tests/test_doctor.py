from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.dependencies import DependencyManager
from aiws.doctor import Doctor
from aiws.state import StateManager


class DoctorTests(unittest.TestCase):
    def test_successful_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_manager = StateManager(state_path=tmp_path / "state.json")
            state_manager.state["applications"] = [
                {
                    "name": "cursor",
                    "install_path": "/opt/Cursor",
                    "version": "1.2.3",
                    "executable": "/usr/bin/cursor",
                }
            ]
            state_manager.save()
            doctor = Doctor(
                dependency_manager=DependencyManager(),
                state_manager=state_manager,
            )
            with (
                patch.object(
                    doctor.dependency_manager, "detect_apt", return_value=True
                ),
                patch.object(
                    doctor.dependency_manager, "detect_sudo", return_value=True
                ),
                patch.object(
                    doctor.dependency_manager, "detect_git", return_value=True
                ),
                patch("aiws.doctor.command_exists", return_value=True),
                patch("aiws.doctor.getpass.getuser", return_value="tester"),
                patch(
                    "aiws.doctor.os.environ",
                    {"PATH": "/usr/bin", "VIRTUAL_ENV": "/venv"},
                ),
                patch("aiws.doctor.platform.release", return_value="6.8.0"),
                patch("aiws.doctor.platform.machine", return_value="x86_64"),
                patch.object(
                    Doctor, "_read_os_release", return_value={"VERSION_ID": "24.04"}
                ),
            ):
                report = doctor.collect()

            self.assertEqual(report["system"]["status"], "ok")
            self.assertEqual(report["dependencies"]["data"]["apt"], True)
            self.assertEqual(
                report["installed_applications"]["data"][0]["name"], "cursor"
            )

    def test_subsystem_failures_are_captured(self) -> None:
        doctor = Doctor()
        with patch.object(
            doctor,
            "_collect_system",
            side_effect=RuntimeError("system failed"),
        ):
            report = doctor.collect()

        self.assertEqual(report["system"]["status"], "error")
        self.assertIn("system failed", report["system"]["error"])

    def test_missing_dependencies_and_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_manager = StateManager(state_path=tmp_path / "state.json")
            doctor = Doctor(state_manager=state_manager)
            with (
                patch.object(
                    doctor.dependency_manager, "detect_apt", return_value=False
                ),
                patch.object(
                    doctor.dependency_manager, "detect_sudo", return_value=False
                ),
                patch.object(
                    doctor.dependency_manager, "detect_git", return_value=False
                ),
                patch("aiws.doctor.command_exists", return_value=False),
                patch("aiws.doctor.getpass.getuser", return_value="tester"),
                patch("aiws.doctor.os.environ", {}),
                patch("aiws.doctor.platform.release", return_value="6.8.0"),
                patch("aiws.doctor.platform.machine", return_value="x86_64"),
                patch.object(Doctor, "_read_os_release", return_value={}),
            ):
                report = doctor.collect()

            self.assertFalse(report["dependencies"]["data"]["apt"])
            self.assertEqual(report["installed_applications"]["data"], [])
