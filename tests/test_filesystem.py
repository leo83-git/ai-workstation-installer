from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiws.filesystem import (
    copy_file,
    create_directory,
    move_file,
    read_json,
    remove_path,
    write_json,
)


class FilesystemTests(unittest.TestCase):
    def test_filesystem_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = {"hello": "world"}
            src = tmp_path / "src.json"
            dst = tmp_path / "nested" / "dst.json"
            write_json(src, data)
            self.assertEqual(read_json(src), data)
            copy_file(src, dst)
            self.assertEqual(read_json(dst), data)
            moved = tmp_path / "moved.json"
            move_file(dst, moved)
            self.assertEqual(read_json(moved), data)
            remove_path(moved)
            self.assertFalse(moved.exists())
            self.assertTrue(create_directory(tmp_path / "created").exists())
