from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiws.installer_manager import InstallerManager
from aiws.state import StateManager


class InstallerManagerTests(unittest.TestCase):
    def test_list_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            state_manager = StateManager(state_path=state_path)
            state_manager.state["applications"] = [
                {"name": "cursor", "version": "1.2.3"}
            ]
            state_manager.save()

            manager = InstallerManager(state_manager=state_manager)

            self.assertEqual(
                manager.list_installed(),
                [{"name": "cursor", "version": "1.2.3"}],
            )

    def test_create_installer_unknown(self) -> None:
        manager = InstallerManager(state_manager=StateManager())

        with self.assertRaises(KeyError):
            manager.create_installer("unknown")
