"""Desktop integration helpers."""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .filesystem import remove_path
from .shell import command_exists, run

LOGGER = logging.getLogger(__name__)

DEFAULT_USER_APPS_DIR = Path("~/.local/share/applications").expanduser()
DEFAULT_USER_ICONS_DIR = Path("~/.local/share/icons/hicolor").expanduser()


def desktop_integration_supported() -> bool:
    """Return whether desktop integration can be performed."""

    return True


@dataclass(frozen=True)
class DesktopEntry:
    """Structured desktop entry data."""

    name: str
    exec_path: Path
    comment: str | None = None
    icon: str | Path | None = None
    terminal: bool = False
    categories: tuple[str, ...] = ("Utility",)
    startup_wm_class: str | None = None

    def render(self) -> str:
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={self.name}",
        ]
        if self.comment:
            lines.append(f"Comment={self.comment}")
        lines.append(f"Exec={self.exec_path}")
        if self.icon:
            lines.append(f"Icon={self.icon}")
        lines.append(f"Terminal={'true' if self.terminal else 'false'}")
        if self.categories:
            lines.append(f"Categories={';'.join(self.categories)};")
        if self.startup_wm_class:
            lines.append(f"StartupWMClass={self.startup_wm_class}")
        lines.append("")
        return "\n".join(lines)


@dataclass
class DesktopManager:
    """Manage desktop entries and icons for user installations."""

    apps_dir: Path = DEFAULT_USER_APPS_DIR
    icons_dir: Path = DEFAULT_USER_ICONS_DIR
    logger: logging.Logger = field(default=LOGGER, repr=False)

    def install_entry(
        self,
        entry_path: Path,
        entry: DesktopEntry,
        icon_path: Path | None = None,
    ) -> None:
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(entry.render())
            temp_path = Path(tmp.name)
        temp_path.replace(entry_path)
        self.logger.info("Desktop entry created: %s", entry_path)
        if icon_path is not None:
            self.install_icon(icon_path, entry.name)
        self.refresh()

    def update_entry(
        self,
        entry_path: Path,
        entry: DesktopEntry,
        icon_path: Path | None = None,
    ) -> None:
        self.install_entry(entry_path, entry, icon_path=icon_path)
        self.logger.info("Desktop entry updated: %s", entry_path)

    def remove_entry(self, entry_path: Path, icon_name: str | None = None) -> None:
        if entry_path.exists() or entry_path.is_symlink():
            remove_path(entry_path)
            self.logger.info("Desktop entry removed: %s", entry_path)
        if icon_name is not None:
            self.remove_icon(icon_name)
        self.refresh()

    def install_icon(self, icon_path: Path, icon_name: str) -> Path | None:
        if not icon_path.exists():
            self.logger.warning("Icon not found, skipping: %s", icon_path)
            return None
        target = self._icon_target(icon_name, icon_path.suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon_path, target)
        self.logger.info("Icon installed: %s", target)
        return target

    def remove_icon(self, icon_name: str) -> None:
        removed = False
        for icon_file in self._icon_targets(icon_name):
            if icon_file.exists():
                remove_path(icon_file)
                removed = True
                self.logger.info("Icon removed: %s", icon_file)
        if removed:
            self.refresh()

    def refresh(self) -> None:
        self._refresh_desktop_database()
        self._refresh_icon_cache()

    def _refresh_desktop_database(self) -> None:
        if command_exists("update-desktop-database"):
            run(["update-desktop-database", str(self.apps_dir)], check=False)
            self.logger.info("Desktop database refreshed")

    def _refresh_icon_cache(self) -> None:
        if command_exists("gtk-update-icon-cache"):
            run(["gtk-update-icon-cache", "-f", str(self.icons_dir)], check=False)
            self.logger.info("Icon cache refreshed")

    def _icon_target(self, icon_name: str, suffix: str) -> Path:
        return self.icons_dir / "apps" / f"{icon_name}{suffix}"

    def _icon_targets(self, icon_name: str) -> list[Path]:
        return [
            self.icons_dir / "apps" / f"{icon_name}{suffix}"
            for suffix in (".png", ".svg", ".xpm", ".ico")
        ]
