"""Shell execution helpers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from shutil import which


@dataclass(frozen=True)
class CommandResult:
    """Result of a shell command."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


def run(command: list[str], check: bool = False) -> CommandResult:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    result = CommandResult(completed.returncode, completed.stdout, completed.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def run_sudo(command: list[str], check: bool = False) -> CommandResult:
    return run(["sudo", *command], check=check)


def command_exists(command: str) -> bool:
    return which(command) is not None


def capture_output(command: list[str]) -> str:
    return run(command).stdout
