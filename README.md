# PMS
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![CI](https://github.com/RDoerfel/pms/workflows/CI/badge.svg)](https://github.com/RDoerfel/pms/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/RDoerfel/pms/branch/main/graph/badge.svg)](https://codecov.io/gh/RDoerfel/pms)
<br>

Pubmed Search tool

## Project Structure

```
├── pms/                # Source code
├── data/               # Data files
├── tests/              # Test files
├── docs/               # Documentation
├── scripts/            # Utility scripts
├── notebooks/          # Jupyter notebooks
└── pyproject.toml      # Poetry configuration
```

## Installation

```bash
# Install the package and dependencies
poetry install
```

## Usage

```python
from pms import some_function
```

## Development

### Setting up the development environment

```bash
# Install all dependencies including development dependencies
poetry install
```

### Testing

```bash
# Run tests
poetry run pytest
```
### Code Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=pms --cov-report=html

# View the HTML coverage report
open htmlcov/index.html  # On macOS
# xdg-open htmlcov/index.html  # On Linux
# start htmlcov/index.html  # On Windows
```
### Formatting

```bash
# Format the code
poetry run black .
```
### Type checking

```bash
# Run type checking
poetry run mypy pms/ tests/
```
### Linting

```bash
# Run linting
poetry run flake8 pms/ tests/
```
## Continuous Integration

This project uses GitHub Actions for continuous integration. The following checks are run on each push and pull request to the main branch:

- Code formatting with Black
- Linting with Flake8
- Type checking with MyPy
- Running tests with pytest
- Code coverage reporting with pytest-cov and Codecov
## License

This project is licensed under the MIT License - see the LICENSE file for details.
