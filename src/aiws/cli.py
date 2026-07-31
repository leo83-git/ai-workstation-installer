"""Command line interface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer

try:
    from rich.console import Console
except ImportError:  # pragma: no cover - environment fallback

    class Console:  # type: ignore[override]
        """Minimal console fallback when Rich submodules are unavailable."""

        def print(self, *args: object, **kwargs: object) -> None:
            print(*args, **kwargs)


from .constants import VERSION
from .doctor import Doctor
from .installer_manager import InstallerManager
from .report import ReportGenerator
from .state import StateManager
from .tools.registry import REGISTRY

console = Console()
app = typer.Typer(add_completion=False, help="AI Workstation Installer")
install_app = typer.Typer(help="Install an application")
update_app = typer.Typer(help="Update an application")
uninstall_app = typer.Typer(help="Uninstall an application")
manager = InstallerManager(state_manager=StateManager())
doctor_service = Doctor()
report_generator = ReportGenerator()


def _get_installer(name: str):
    try:
        return manager.create_installer(name)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _invoke_tool(tool_name: str, handler: Callable[[Any], Any]) -> None:
    installer = _get_installer(tool_name)
    result = handler(installer)
    if isinstance(result, str):
        console.print(result)
    elif result is not None:
        console.print(result)


def _register_tool_commands(tool_name: str) -> None:
    @install_app.command(tool_name)
    def install_tool() -> None:
        """Install a registered application."""

        _invoke_tool(tool_name, lambda installer: installer.install())

    @update_app.command(tool_name)
    def update_tool() -> None:
        """Update a registered application."""

        _invoke_tool(tool_name, lambda installer: installer.update())

    @uninstall_app.command(tool_name)
    def uninstall_tool() -> None:
        """Uninstall a registered application."""

        _invoke_tool(tool_name, lambda installer: installer.uninstall())


for tool_name in REGISTRY:
    _register_tool_commands(tool_name)


@app.command()
def list() -> None:  # noqa: A003
    """List installed applications."""

    installed = manager.list_installed()
    if not installed:
        console.print("No applications installed.")
        return
    for item in installed:
        name = item.get("name", "unknown")
        version = item.get("version", "unknown")
        console.print(f"{name}: {version}")


@app.command()
def version() -> None:
    """Print the application version."""

    console.print(VERSION)


@app.command()
def report() -> None:
    """Placeholder report command."""

    console.print("report: phase 1 placeholder")


@app.command()
def doctor(
    tool_name: str | None = typer.Argument(
        None, help="Optional registered application name."
    ),
    json: bool = typer.Option(
        False, "--json", help="Output JSON report."
    ),  # noqa: A002
) -> None:
    """Run workstation diagnostics."""

    if tool_name is not None:
        _invoke_tool(tool_name, lambda installer: installer.doctor())
        return
    report = doctor_service.collect()
    if json:
        console.print(report_generator.render_json(report))
        return
    console.print(report_generator.render_rich(report))


@app.command()
def prepare() -> None:
    """Placeholder prepare command."""

    console.print("prepare: phase 1 placeholder")


def _version_callback(value: bool) -> None:
    if value:
        console.print(VERSION)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version_flag: bool = typer.Option(
        False,
        "--version",
        help="Show the application version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """AI Workstation Installer entry point."""

    if version_flag:
        return


app.add_typer(install_app, name="install")
app.add_typer(update_app, name="update")
app.add_typer(uninstall_app, name="uninstall")
