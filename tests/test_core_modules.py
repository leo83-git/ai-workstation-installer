from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from aiws import VERSION, __version__
from aiws.backup import create_backup_plan
from aiws.config import AppConfig
from aiws.desktop import desktop_integration_supported
from aiws.doctor import run_doctor_checks
from aiws.installer import orchestrate_installation
from aiws.logger import configure_logging
from aiws.report import MarkdownReport
from aiws.tools.base import ToolInstaller
from aiws.tools.registry import REGISTRY


class CoreModuleTests(unittest.TestCase):
    def test_version_exports(self) -> None:
        self.assertEqual(VERSION, __version__)

    def test_config_default_state_file(self) -> None:
        config = AppConfig()
        self.assertTrue(str(config.state_file).endswith("aiws/state.json"))

    def test_logger_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "aiws.log"
            logger = configure_logging(log_file)
            self.assertIsInstance(logger, logging.Logger)
            self.assertGreaterEqual(len(logger.handlers), 2)
            self.assertTrue(log_file.parent.exists())

    def test_report_render(self) -> None:
        report = MarkdownReport("Title")
        report.add_section("Body")
        self.assertIn("# Title", report.render())
        self.assertIn("Body", report.render())

    def test_placeholder_modules(self) -> None:
        self.assertEqual(create_backup_plan(), {"status": "placeholder"})
        self.assertFalse(desktop_integration_supported())
        self.assertEqual(run_doctor_checks(), [])
        self.assertEqual(orchestrate_installation(), {"status": "phase_1_only"})
        self.assertEqual(REGISTRY, {})

    def test_tool_installer_interface(self) -> None:
        class DemoInstaller(ToolInstaller):
            def detect(self) -> bool:
                return True

            def install(self) -> None:
                return None

            def update(self) -> None:
                return None

            def uninstall(self) -> None:
                return None

            def doctor(self) -> list[str]:
                return []

        installer = DemoInstaller()
        self.assertTrue(installer.detect())
        self.assertEqual(installer.doctor(), [])
