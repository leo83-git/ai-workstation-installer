from __future__ import annotations

import unittest

from aiws.release import get_release_metadata
from aiws.version import VERSION, get_version


class VersionTests(unittest.TestCase):
    def test_version_retrieval(self) -> None:
        self.assertEqual(get_version(), VERSION)

    def test_metadata_access(self) -> None:
        metadata = get_release_metadata()
        self.assertEqual(metadata.version, VERSION)
        self.assertTrue(metadata.application_name)
        self.assertTrue(metadata.author)
        self.assertTrue(metadata.license)
        self.assertTrue(metadata.repository)
        self.assertTrue(metadata.supported_platform)
