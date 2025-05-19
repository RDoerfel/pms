# PMS - PubMed Search Tool
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![CI](https://github.com/RDoerfel/pms/workflows/CI/badge.svg)](https://github.com/RDoerfel/pms/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/RDoerfel/pms/branch/main/graph/badge.svg)](https://codecov.io/gh/RDoerfel/pms)
<br>

PMS is a tool for scraping PubMed articles and storing them in a structured format. It includes project management capabilities that allow you to organize searches and avoid duplicates.

## Features

- Search PubMed using complex queries
- Extract titles, abstracts, authors, publication dates, and more
- Project-based management of searches
- Deduplication within projects
- Export data in multiple formats (JSONL, JSON, CSV)
- Configurable rate limiting to comply with NCBI's policies

## Project Structure

```
├── pms/                # Source code
│   ├── api/            # PubMed API client
│   ├── cli/            # Command-line interface
│   ├── config/         # Configuration management
│   ├── models/         # Data models
│   ├── project/        # Project management
│   ├── storage/        # Storage mechanisms
│   └── utils/          # Utility functions
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

## Configuration

Before using PMS, you should configure your email (required by NCBI):

```bash
# Set your email for PubMed API
pms config set api email your.email@example.com
```

You can also configure other settings:

```bash
# List all configuration options
pms config list

# Set API key (optional, for higher rate limits)
pms config set api api_key your-api-key

# Set custom data directory
pms config set storage data_dir /path/to/data/dir
```

## Usage

### Creating a Project

```bash
# Create a new project
pms create "My Research Project" --description "Research on cancer biomarkers"

# List all projects
pms list
```

### Searching PubMed

```bash
# Search PubMed for a project (using project ID)
pms search abc123 "cancer AND biomarkers" --max-results 200

# Search with date range
pms search abc123 "cancer AND biomarkers" --date-range 2020/01/01:2023/12/31

# Search with batch size (for large queries)
pms search abc123 "cancer AND biomarkers" --batch-size 50
```

### Managing Project Data

```bash
# Count articles in a project
pms count abc123

# Export project articles to a file
pms export abc123 output.jsonl

# Export in different formats
pms export abc123 output.json --format json
pms export abc123 output.csv --format csv

# Remove a project
pms remove abc123
```

## Query Examples

PMS uses the standard PubMed query syntax:

- Simple keyword search: `cancer`
- Multiple keywords (AND): `cancer AND biomarkers`
- Multiple keywords (OR): `cancer OR tumor`
- Phrase search: `"breast cancer"`
- Field-specific search: `Smith[Author] AND cancer[Title]`
- MeSH terms: `"Neoplasms"[MeSH]`
- Complex queries: `("breast cancer"[Title] OR "breast neoplasms"[MeSH]) AND biomarkers[Title/Abstract] AND 2020:2023[DP]`

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

### Formatting and Linting

```bash
# Format the code
poetry run black .

# Run type checking
poetry run mypy pms/ tests/

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
