"""Command line interface."""

from __future__ import annotations

import typer

try:
    from rich.console import Console
except ImportError:  # pragma: no cover - environment fallback

    class Console:  # type: ignore[override]
        """Minimal console fallback when Rich submodules are unavailable."""

        def print(self, *args: object, **kwargs: object) -> None:
            print(*args, **kwargs)


from .constants import VERSION

console = Console()
app = typer.Typer(add_completion=False, help="AI Workstation Installer")


@app.command()
def install() -> None:
    """Placeholder install command."""

    console.print("install: phase 1 placeholder")


@app.command()
def update() -> None:
    """Placeholder update command."""

    console.print("update: phase 1 placeholder")


@app.command()
def uninstall() -> None:
    """Placeholder uninstall command."""

    console.print("uninstall: phase 1 placeholder")


@app.command()
def doctor() -> None:
    """Placeholder doctor command."""

    console.print("doctor: phase 1 placeholder")


@app.command()
def report() -> None:
    """Placeholder report command."""

    console.print("report: phase 1 placeholder")


@app.command()
def prepare() -> None:
    """Placeholder prepare command."""

    console.print("prepare: phase 1 placeholder")


@app.command()
def list() -> None:  # noqa: A003
    """List installed applications."""

    console.print("No applications installed.")


@app.command()
def version() -> None:
    """Print the application version."""

    console.print(VERSION)


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
