from __future__ import annotations

import json
import unittest

from aiws.report import ReportGenerator


class ReportGeneratorTests(unittest.TestCase):
    def test_rich_output(self) -> None:
        report = {"title": "Demo", "system": {"kernel": "6.8.0"}}
        rendered = ReportGenerator().render_rich(report)
        self.assertIn("Demo", rendered)
        self.assertIn("System", rendered)

    def test_json_output(self) -> None:
        report = {"title": "Demo", "system": {"kernel": "6.8.0"}}
        rendered = ReportGenerator().render_json(report)
        self.assertEqual(json.loads(rendered), report)

    def test_serialization(self) -> None:
        report = {"title": "Demo", "value": object()}
        rendered = ReportGenerator().render_json(report)
        data = json.loads(rendered)
        self.assertEqual(data["title"], "Demo")
