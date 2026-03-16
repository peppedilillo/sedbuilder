### Setup

Clone the repository and install with development dependencies:

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
# next line will route queries to test server. 
# use only on SSDC internal network 
source dev.env 
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

### Building and shipping Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs gh-deploy
```