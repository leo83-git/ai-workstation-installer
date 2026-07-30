# AI Workstation Installer

AI Workstation Installer is a Python 3.12+ project scaffold for building a clean,
production-ready installer experience on Ubuntu 24.04 LTS.

## Features

- Modern `src/`-layout Python package
- Typer-based CLI
- Shared version metadata
- State, filesystem, shell, dependency, logging, and reporting foundations
- Unit tests for the Phase 1 foundation
- Development tooling for linting, formatting, import sorting, and pre-commit

## Requirements

- Python 3.12+
- `pip`
- A virtual environment such as `.venv`

## Installation

### Create a virtual environment

```bash
python3 -m venv .venv
```

### Activate it

```bash
. .venv/bin/activate
```

### Install dependencies

```bash
pip install -e .[dev]
```

## Running Tests

```bash
pytest -q
pytest --cov=src/aiws --cov-report=term-missing
```

## Running Ruff

```bash
ruff check .
```

## Running Black

```bash
black --check .
black .
```

## Running pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## Project Structure

```text
src/aiws/
tests/
```

## CLI Commands

```bash
aiws install
aiws update
aiws uninstall
aiws doctor
aiws report
aiws prepare
aiws list
aiws version
aiws --version
```

## Development Workflow

1. Create and activate `.venv`
2. Install `.[dev]`
3. Run `ruff check .`
4. Run `black --check .`
5. Run `pytest --cov=src/aiws --cov-report=term-missing`
6. Use `pre-commit run --all-files` before committing

