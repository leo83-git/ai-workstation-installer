from __future__ import annotations

import unittest
from unittest.mock import patch

from aiws.dependencies import DependencyManager


class DependencyManagerTests(unittest.TestCase):
    def test_dependency_manager_detect(self) -> None:
        manager = DependencyManager()
        with (
            patch.object(manager, "detect_python", return_value=True),
            patch.object(manager, "detect_git", return_value=True),
            patch.object(manager, "detect_sudo", return_value=True),
            patch.object(manager, "detect_internet", return_value=True),
            patch.object(manager, "detect_disk_space", return_value=True),
            patch.object(manager, "detect_apt", return_value=True),
        ):
            status = manager.detect()
        self.assertTrue(status.python)
        self.assertTrue(status.git)
        self.assertTrue(status.sudo)
        self.assertTrue(status.internet)
        self.assertTrue(status.disk_space_ok)
        self.assertTrue(status.apt)
