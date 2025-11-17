# sedbuilder

A Python client library for the ASI-SSDC SED Builder API.

## Overview

**sedbuilder** provides an interface to the ASI Space Science Data Center's SED Builder REST API for retrieving Spectral Energy Distribution data for astronomical sources.

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

## Documentation

Full documentation available at: ..

## Development

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
pre-commit install
pytest
```

## License

GNU GENERAL PUBLIC LICENSE - see [LICENSE](LICENSE) file for details.
