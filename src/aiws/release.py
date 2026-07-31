"""Release metadata helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .version import get_version


@dataclass(frozen=True)
class ReleaseMetadata:
    """Metadata describing the current release."""

    application_name: str
    version: str
    author: str
    license: str
    repository: str
    supported_platform: str


def get_release_metadata() -> ReleaseMetadata:
    """Return the current release metadata."""

    return ReleaseMetadata(
        application_name="AI Workstation Installer",
        version=get_version(),
        author="OpenAI",
        license="MIT",
        repository="https://github.com/leo83-git/ai-workstation-installer",
        supported_platform="Ubuntu 24.04 LTS",
    )
