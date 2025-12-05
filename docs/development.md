### Setup

Clone the repository and install with development dependencies:

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
```

### Pre-commit Hooks

Install pre-commit hooks to automatically format code before commits:

```bash
pre-commit install
```

This runs `black` (line length 120) and `isort` (Google profile) automatically.

### Running Tests

```bash
pytest
```

You must first `cd` into the project directory.

### Building Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
```