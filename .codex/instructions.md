# AI Workstation OInstaller - Codex Instructions

You are the primary software engineer for this repository.

## General

- Write production-quality Python.
- Target Ubuntu 24.04 LTS.
- Prefer readability over cleverness.
- Keep modules small.
- Add type hints.
- Add docstrings.
- Follow PEP 8.
- Keep functions focused.

---

## Before Coding

Always:

1. Understand existing code.
2. Reuse existing modules.
3. Avoid duplication.
4. Keep architecture simple.

---

## Git

Never:

- push automatically
- commit automatically
- delete branches

Only commit when explicitly requested.

Never rewrite Git history.

---

## Code Quality

Always:

- run pytest
- fix failing tests
- run Ruff if configured
- run Black if configured

---

## File Safety

Never overwrite configuration files without asking.

Never delete user files.

Never remove tests.

---

## Python

Prefer:

- pathlib
- dataclasses
- typing
- subprocess.run()
- logging

Avoid unnecessary dependencies.

---

## Error Handling

Never ignore exceptions.

Always provide meaningful error messages.

Rollback partially completed operations whenever possible.

---

## Installer

Every installer should implement:

detect()

install()

update()

uninstall()

doctor()

---

## Documentation

Whenever functionality changes:

Update README if necessary.

---

## Output

At the end of every task provide:

- files changed
- tests executed
- warnings
- remaining TODOs
