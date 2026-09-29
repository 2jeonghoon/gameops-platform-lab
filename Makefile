.PHONY: test lint format-check verify

test:
	uv run pytest

lint:
	uv run ruff check app tests

format-check:
	uv run ruff format --check app tests

verify: lint format-check test
