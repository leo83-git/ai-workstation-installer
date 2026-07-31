from __future__ import annotations

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from aiws.download_manager import (
    DownloadManager,
    InterruptedDownloadError,
    InvalidURLError,
    NetworkDownloadError,
)


class _Handler(BaseHTTPRequestHandler):
    payload = b"hello world"

    def do_GET(self):  # noqa: N802
        if self.path == "/file.bin":
            range_header = self.headers.get("Range")
            if range_header == "bytes=6-":
                body = self.payload[6:]
                self.send_response(206)
                self.send_header("Content-Length", str(len(body)))
                self.send_header(
                    "Content-Range",
                    f"bytes 6-{len(self.payload) - 1}/{len(self.payload)}",
                )
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.payload)))
            self.end_headers()
            self.wfile.write(self.payload)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args, **_kwargs):
        return


class DownloadManagerTests(unittest.TestCase):
    def _serve(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_download_success(self) -> None:
        server, thread = self._serve()
        try:
            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                destination = tmp_path / "downloads" / "file.bin"
                manager = DownloadManager(timeout=5, retry_count=0, chunk_size=4)
                result = manager.download(
                    f"http://127.0.0.1:{server.server_address[1]}/file.bin",
                    destination,
                )
                self.assertEqual(result, destination)
                self.assertEqual(destination.read_bytes(), _Handler.payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

    def test_download_skips_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            destination = tmp_path / "file.bin"
            destination.write_bytes(b"existing")
            manager = DownloadManager()
            result = manager.download("http://example.com/file.bin", destination)
            self.assertEqual(result, destination)
            self.assertEqual(destination.read_bytes(), b"existing")

    def test_download_resumes_partial_file(self) -> None:
        server, thread = self._serve()
        try:
            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                destination = tmp_path / "file.bin"
                part_path = destination.with_name(destination.name + ".part")
                part_path.write_bytes(b"hello ")
                manager = DownloadManager(timeout=5, retry_count=0, chunk_size=4)
                result = manager.download(
                    f"http://127.0.0.1:{server.server_address[1]}/file.bin",
                    destination,
                )
                self.assertEqual(result, destination)
                self.assertEqual(destination.read_bytes(), _Handler.payload)
                self.assertFalse(part_path.exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

    def test_invalid_url(self) -> None:
        manager = DownloadManager()
        with self.assertRaises(InvalidURLError):
            manager.download("ftp://example.com/file.bin", Path("/tmp/file.bin"))

    def test_network_error(self) -> None:
        manager = DownloadManager(retry_count=0)
        with patch("aiws.download_manager.urlopen", side_effect=URLError("boom")):
            with self.assertRaises(NetworkDownloadError):
                manager.download("http://example.com/file.bin", Path("/tmp/file.bin"))

    def test_interrupted_download(self) -> None:
        manager = DownloadManager(retry_count=0)

        def raise_timeout(*_args, **_kwargs):
            raise TimeoutError("timed out")

        with patch("aiws.download_manager.urlopen", side_effect=raise_timeout):
            with self.assertRaises(InterruptedDownloadError):
                manager.download("http://example.com/file.bin", Path("/tmp/file.bin"))
