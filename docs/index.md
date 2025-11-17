# sedbuilder

A Python client library for the ASI-SSDC SED Builder API.

## Overview

The **sedbuilder** package provides a simple interface to the ASI Space Science Data Center's SED Builder REST API for retrieving Spectral Energy Distribution data for astronomical sources.

The SSDC SED Builder is a web-based program developed at the ASI Space Science Data Center to produce and display the Spectral Energy Distribution (SED) of astrophysical sources. The tool combines data from several missions and experiments, both ground and space-based, together with catalogs and archival data.

## Installation

```bash
pip install sedbuilder
```

## Quick Start

```python
from sedbuilder import get_data

# Query SED data for astronomical coordinates (RA, Dec in degrees)
data = get_data(ra=194.04625, dec=-5.789167)
```

## Development

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

### Building Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
```

## API Reference

See the [API Reference](api.md) for detailed documentation of all functions.
