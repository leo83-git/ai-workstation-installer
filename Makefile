.PHONY: install dev-install test coverage lint format check clean

install:
	python3 -m pip install -e .

dev-install:
	python3 -m pip install -e .[dev]

test:
	pytest -q

coverage:
	pytest --cov=src/aiws --cov-report=term-missing

lint:
	ruff check .
	isort --check-only .
	black --check .

format:
	isort .
	black .

check: lint test coverage

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

