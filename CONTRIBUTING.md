# Contributing to usac-data

Thanks for your interest in contributing! Here's how to get started.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) to manage the development
environment. `uv sync` creates `.venv` and installs the exact versions pinned in
`uv.lock`, which is the same set CI runs against.

```bash
git clone https://github.com/sgentzen/usac-data.git
cd usac-data
uv sync --all-extras
```

If you change anything under `[project.dependencies]` or
`[project.optional-dependencies]`, regenerate the lock and commit it alongside
the change:

```bash
uv lock
```

## Development workflow

1. Create a branch for your change
2. Make your changes
3. Run the checks:

```bash
uv run pytest         # tests
uv run ruff check .   # linting (src/ and tests/)
uv run ruff format .  # formatting
uv run mypy src/      # type checking
```

4. Open a pull request

## Code style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type hints are required on all public functions (mypy strict mode)
- Docstrings on all public classes and methods

## Adding a new dataset

1. Create a new file in `src/usac_data/datasets/`
2. Subclass `DatasetMeta` and set `dataset_id`, `name`, `description`
3. Add known field names as class attributes
4. Add convenience query methods as `@classmethod`s
5. Re-export from `src/usac_data/datasets/__init__.py` and `src/usac_data/__init__.py`
6. Add tests in `tests/`

## Releasing

Maintainers: see [docs/releasing.md](docs/releasing.md). Releases publish to
PyPI from a GitHub Release via Trusted Publishing; pushing a tag alone does not
publish anything.

## Reporting issues

Open an issue at https://github.com/sgentzen/usac-data/issues with:
- What you expected to happen
- What actually happened
- Steps to reproduce
