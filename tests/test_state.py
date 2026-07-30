from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiws.state import StateManager


class StateTests(unittest.TestCase):
    def test_state_manager_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            manager = StateManager(state_path=state_path)
            manager.record_application({"name": "demo"})
            manager.load()
            self.assertEqual(manager.list_installed(), [{"name": "demo"}])
            manager.remove_application("demo")
            self.assertEqual(manager.list_installed(), [])
