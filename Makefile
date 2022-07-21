.PHONY: quality style test

# Check that source code meets quality standards

quality:
	black --check --line-length 119 --target-version py36 tests src examples
	isort --check-only tests src examples
	flake8 tests src

# Format source code automatically

style:
	black --line-length 119 --target-version py36 tests src examples
	isort tests src examples

# Run tests for the library

test:
	python -m pytest -n auto --dist=loadfile -s -v ./tests/
