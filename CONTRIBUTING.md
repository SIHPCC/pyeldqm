# Contributing to pyELDQM

Thank you for your interest in contributing!  
This document describes the workflow, coding standards, and testing requirements.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Running Tests](#running-tests)
5. [Submitting a Pull Request](#submitting-a-pull-request)
6. [Reporting Issues](#reporting-issues)

---

## Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/pyeldqm.git
cd pyeldqm

# 2. Create a virtual environment (Python ≥ 3.9)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install in editable mode with all extras
pip install -e ".[full]"

# 4. Install dev tools
pip install pytest pytest-cov ruff
```

---

## Project Structure

```
pyELDQM/
├── core/              # Pure-Python scientific library (no Dash dependency)
│   ├── dispersion_models/
│   ├── fire_models/
│   ├── meteorology/
│   ├── source_models/
│   ├── evacuation/
│   ├── population/
│   ├── utils/
│   └── visualization/
├── app/               # Dash web-application layer
│   ├── callbacks/
│   ├── components/
│   └── layout/
├── tests/             # pytest test suite
├── configs/           # Example YAML scenarios
└── data/              # Reference data (not shipped in wheel)
```

`core/` must remain import-able without Dash installed.  
All Dash-specific code belongs in `app/`.

---

## Coding Standards

- **Formatter / linter**: [Ruff](https://docs.astral.sh/ruff/) — `ruff check .`  
  Configuration is in `pyproject.toml` (`[tool.ruff]`).
- **Line length**: 100 characters.
- **Type hints**: Required on all public functions (PEP 484 / PEP 526).
- **Docstrings**: NumPy docstring style for public functions.
- **Logging**: Use `logging.getLogger(__name__)` — never `print()` for diagnostics.
- **Constants**: Named with `UPPER_SNAKE_CASE`; provide a units comment.
- **No `sys.path` hacks**: Use `pyproject.toml` package discovery.

---

## Running Tests

```bash
# All tests with coverage report
pytest tests/ --cov=core --cov-report=term-missing

# Fast, quiet
pytest tests/ -q

# Single file
pytest tests/test_dispersion_utils.py -v
```

Add new tests in `tests/` for every bug fix and new feature.  
Aim to keep `core/` coverage above **70 %**.

---

## Submitting a Pull Request

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes, including tests.
3. Run `ruff check .` and `pytest tests/` — both must pass.
4. Commit with a clear message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add PASQUILL class G support
   fix: correct MW_AIR constant in heavy gas model
   docs: add wind profile docstring
   ```
5. Open a pull request against `main` with a description of the change and any
   relevant issue numbers.

---

## Reporting Issues

Please open a GitHub Issue with:
- A minimal reproducible example
- The Python version and OS
- Package version (`python -c "import pyeldqm; print(pyeldqm.__version__)"`)
- The full traceback if applicable

---

*Happy modelling!*
