from __future__ import annotations

import unittest

from typer.testing import CliRunner

from aiws.cli import app
from aiws.constants import VERSION
from aiws.tools.registry import REGISTRY

runner = CliRunner()


class CLITests(unittest.TestCase):
    def test_cli_version_command(self) -> None:
        result = runner.invoke(app, ["version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(VERSION, result.output)

    def test_cli_list_command(self) -> None:
        result = runner.invoke(app, ["list"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No applications installed.", result.output)

    def test_cli_help_exposes_documented_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        for command in [
            "install",
            "update",
            "uninstall",
            "doctor",
            "report",
            "prepare",
            "list",
            "version",
        ]:
            self.assertIn(command, result.output)

    def test_cursor_registry_present(self) -> None:
        self.assertIn("cursor", REGISTRY)
