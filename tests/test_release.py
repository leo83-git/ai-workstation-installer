from __future__ import annotations

import unittest

from aiws.release import get_release_metadata
from aiws.version import VERSION


class ReleaseMetadataTests(unittest.TestCase):
    def test_expected_fields_exist(self) -> None:
        metadata = get_release_metadata()
        self.assertEqual(metadata.application_name, "AI Workstation Installer")
        self.assertEqual(metadata.version, VERSION)
        self.assertEqual(metadata.author, "OpenAI")
        self.assertEqual(metadata.license, "MIT")
        self.assertTrue(metadata.repository.startswith("https://"))
        self.assertIn("Ubuntu", metadata.supported_platform)

    def test_version_consistency(self) -> None:
        metadata = get_release_metadata()
        self.assertEqual(metadata.version, VERSION)
