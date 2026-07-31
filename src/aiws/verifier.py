"""File verification helpers."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class VerificationError(RuntimeError):
    """Base error for verification failures."""


class MissingChecksumError(VerificationError):
    """Raised when a checksum value is missing or invalid."""


class VerificationFailedError(VerificationError):
    """Raised when a file checksum does not match."""


@dataclass(frozen=True)
class Verifier:
    """Stream file content and verify SHA256 checksums."""

    chunk_size: int = 1024 * 1024

    def verify_file(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify that a file matches an expected SHA256 checksum."""

        self._validate_checksum(expected_sha256)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        LOGGER.info("Verification started for %s", file_path)
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            while True:
                chunk = handle.read(self.chunk_size)
                if not chunk:
                    break
                digest.update(chunk)

        actual = digest.hexdigest()
        expected = expected_sha256.lower()
        if actual != expected:
            LOGGER.error("Verification failed for %s", file_path)
            raise VerificationFailedError(
                f"Checksum mismatch for {file_path}: expected {expected}, got {actual}"
            )

        LOGGER.info("Verification succeeded for %s", file_path)
        return True

    def _validate_checksum(self, checksum: str) -> None:
        if checksum is None or not checksum.strip():
            raise MissingChecksumError("Expected SHA256 checksum is required")
        if not re.fullmatch(r"[A-Fa-f0-9]{64}", checksum.strip()):
            raise MissingChecksumError(
                "Expected SHA256 checksum must be 64 hex characters"
            )
