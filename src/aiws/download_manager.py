"""Shared download utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)


class DownloadError(RuntimeError):
    """Base error for download failures."""


class InvalidURLError(DownloadError):
    """Raised when a URL is invalid or unsupported."""


class NetworkDownloadError(DownloadError):
    """Raised when a download fails due to network issues."""


class InterruptedDownloadError(DownloadError):
    """Raised when a download is interrupted before completion."""


@dataclass
class DownloadManager:
    """Download files with progress reporting and resume support."""

    timeout: float = 30.0
    retry_count: int = 2
    chunk_size: int = 1024 * 1024

    def download(self, url: str, destination: Path) -> Path:
        parsed = self._validate_url(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            return destination

        part_path = self._part_path(destination)
        for attempt in range(self.retry_count + 1):
            try:
                return self._download_once(parsed, url, destination, part_path)
            except InterruptedDownloadError:
                if destination.exists():
                    return destination
                if attempt >= self.retry_count:
                    raise
            except (HTTPError, URLError, TimeoutError) as exc:
                if attempt >= self.retry_count:
                    raise NetworkDownloadError(str(exc)) from exc
                time.sleep(0)
        raise DownloadError(f"Failed to download {url}")

    def _download_once(
        self, parsed: Any, url: str, destination: Path, part_path: Path
    ) -> Path:
        headers: dict[str, str] = {}
        mode = "wb"
        start = 0
        if part_path.exists():
            start = part_path.stat().st_size
            if start > 0:
                headers["Range"] = f"bytes={start}-"
                mode = "ab"

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                total = self._content_length(response, start)
                if start and response.status == 200:
                    mode = "wb"
                    start = 0
                with Progress(
                    TextColumn("{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                    transient=True,
                ) as progress:
                    task = progress.add_task(
                        parsed.path.rsplit("/", 1)[-1] or "download", total=total
                    )
                    with part_path.open(mode) as handle:
                        downloaded = start
                        while True:
                            chunk = response.read(self.chunk_size)
                            if not chunk:
                                break
                            handle.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, completed=downloaded)
                part_path.replace(destination)
                return destination
        except HTTPError as exc:
            if exc.code == 416 and destination.exists():
                return destination
            raise
        except TimeoutError as exc:
            raise InterruptedDownloadError(str(exc)) from exc
        except URLError as exc:
            raise NetworkDownloadError(str(exc)) from exc
        except OSError as exc:
            raise InterruptedDownloadError(str(exc)) from exc

    def _validate_url(self, url: str):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidURLError(f"Unsupported URL: {url}")
        return parsed

    def _part_path(self, destination: Path) -> Path:
        return destination.with_name(destination.name + ".part")

    def _content_length(self, response: Any, start: int) -> int | None:
        content_length = response.headers.get("Content-Length")
        if content_length is None:
            return None
        try:
            return int(content_length) + start
        except ValueError:
            return None
