# Contributing to usac-data

Thanks for your interest in contributing! Here's how to get started.

## Setup

```bash
git clone https://github.com/sgentzen/usac-data.git
cd usac-data
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Development workflow

1. Create a branch for your change
2. Make your changes
3. Run the checks:

```bash
pytest                # tests
ruff check src/       # linting
ruff format src/      # formatting
mypy src/             # type checking
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

## Reporting issues

Open an issue at https://github.com/sgentzen/usac-data/issues with:
- What you expected to happen
- What actually happened
- Steps to reproduce
