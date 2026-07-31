# Release Instructions

## Create a virtual environment

```bash
python3 -m venv .venv
```

## Activate it

```bash
. .venv/bin/activate
```

## Install dependencies

```bash
pip install -e .[dev]
```

## Run verification

```bash
pytest
```

## Build distributions

```bash
python -m build
```

## Install locally

```bash
pip install dist/*.whl
```

## Uninstall locally

```bash
pip uninstall aiws
```

## Publish a GitHub Release

1. Create and push a version tag.
2. Upload the built `sdist` and wheel artifacts to the GitHub Release.
3. Publish the release notes from `CHANGELOG.md` and `RELEASE.md`.

