from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from aiws.verifier import (
    MissingChecksumError,
    VerificationFailedError,
    Verifier,
)


class VerifierTests(unittest.TestCase):
    def test_valid_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.bin"
            path.write_bytes(b"hello world")
            checksum = hashlib.sha256(b"hello world").hexdigest()

            self.assertTrue(Verifier().verify_file(path, checksum))

    def test_invalid_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.bin"
            path.write_bytes(b"hello world")

            with self.assertRaises(VerificationFailedError):
                Verifier().verify_file(path, "0" * 64)

    def test_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.bin"
            checksum = "0" * 64

            with self.assertRaises(FileNotFoundError):
                Verifier().verify_file(path, checksum)

    def test_malformed_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.bin"
            path.write_bytes(b"hello")

            with self.assertRaises(MissingChecksumError):
                Verifier().verify_file(path, "not-a-checksum")

    def test_empty_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.bin"
            path.write_bytes(b"hello")

            with self.assertRaises(MissingChecksumError):
                Verifier().verify_file(path, "")

    def test_large_file_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.bin"
            payload = b"a" * (2 * 1024 * 1024 + 17)
            path.write_bytes(payload)
            checksum = hashlib.sha256(payload).hexdigest()

            verifier = Verifier(chunk_size=64 * 1024)
            self.assertTrue(verifier.verify_file(path, checksum))
