from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiws.desktop import DesktopEntry, DesktopManager


class DesktopManagerTests(unittest.TestCase):
    def test_create_desktop_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            entry_path = tmp_path / "apps" / "demo.desktop"
            icon = tmp_path / "icon.png"
            icon.write_bytes(b"icon")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )
            entry = DesktopEntry(
                name="Demo",
                exec_path=Path("/opt/demo/bin/demo"),
                comment="Demo app",
                icon="Demo",
            )

            with (
                patch("aiws.desktop.command_exists", return_value=False),
                patch("aiws.desktop.run") as run_mock,
            ):
                manager.install_entry(entry_path, entry, icon_path=icon)

            self.assertTrue(entry_path.exists())
            self.assertIn("Name=Demo", entry_path.read_text(encoding="utf-8"))
            self.assertFalse(run_mock.called)

    def test_update_desktop_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            entry_path = tmp_path / "apps" / "demo.desktop"
            entry_path.parent.mkdir(parents=True, exist_ok=True)
            entry_path.write_text("old", encoding="utf-8")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )
            entry = DesktopEntry(name="Demo", exec_path=Path("/opt/demo/bin/demo"))

            with (
                patch("aiws.desktop.command_exists", return_value=False),
                patch("aiws.desktop.run"),
            ):
                manager.update_entry(entry_path, entry)

            self.assertIn("Name=Demo", entry_path.read_text(encoding="utf-8"))

    def test_remove_desktop_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            entry_path = tmp_path / "apps" / "demo.desktop"
            entry_path.parent.mkdir(parents=True, exist_ok=True)
            entry_path.write_text("demo", encoding="utf-8")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )

            with (
                patch("aiws.desktop.command_exists", return_value=False),
                patch("aiws.desktop.run"),
            ):
                manager.remove_entry(entry_path)

            self.assertFalse(entry_path.exists())

    def test_install_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            icon = tmp_path / "icon.png"
            icon.write_bytes(b"icon")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )

            result = manager.install_icon(icon, "Demo")

            self.assertIsNotNone(result)
            self.assertTrue(result.exists())

    def test_remove_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            icon_file = tmp_path / "icons" / "apps" / "Demo.png"
            icon_file.parent.mkdir(parents=True, exist_ok=True)
            icon_file.write_bytes(b"icon")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )

            with (
                patch("aiws.desktop.command_exists", return_value=False),
                patch("aiws.desktop.run"),
            ):
                manager.remove_icon("Demo")

            self.assertFalse(icon_file.exists())

    def test_refresh_methods(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )

            with patch("aiws.desktop.command_exists", side_effect=lambda cmd: True):
                with patch("aiws.desktop.run") as run_mock:
                    manager.refresh()

            self.assertGreaterEqual(run_mock.call_count, 2)

    def test_missing_icon_handling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )

            result = manager.install_icon(tmp_path / "missing.png", "Demo")
            self.assertIsNone(result)

    def test_idempotent_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            entry_path = tmp_path / "apps" / "demo.desktop"
            icon = tmp_path / "icon.png"
            icon.write_bytes(b"icon")
            manager = DesktopManager(
                apps_dir=tmp_path / "apps",
                icons_dir=tmp_path / "icons",
            )
            entry = DesktopEntry(name="Demo", exec_path=Path("/opt/demo/bin/demo"))

            with (
                patch("aiws.desktop.command_exists", return_value=False),
                patch("aiws.desktop.run"),
            ):
                manager.install_entry(entry_path, entry, icon_path=icon)
                manager.install_entry(entry_path, entry, icon_path=icon)
                manager.remove_entry(entry_path)
                manager.remove_entry(entry_path)

            self.assertFalse(entry_path.exists())
