from __future__ import annotations

import unittest

from aiws.shell import capture_output, command_exists, run


class ShellTests(unittest.TestCase):
    def test_shell_helpers(self) -> None:
        self.assertTrue(command_exists("python3"))
        result = run(["python3", "-c", "print('ok')"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "ok")
        self.assertEqual(capture_output(["python3", "-c", "print('hi')"]).strip(), "hi")
