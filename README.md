# sedbuilder

The **sedbuilder** package implements a Python interface to the ASI Space Science Data Center's SED Builder REST API.

## Overview

This package provides programmatic access to multi-wavelength spectral energy distribution (SED) data from catalogs, surveys, and archival observations across the electromagnetic spectrum.
It is based on [SED Builder](https://tools.ssdc.asi.it/SED/), a software developed at the ASI-SSDC to produce and display the SED data over the web.

## Installation

```bash
pip install ssdc-sedbuilder
```

## Quick Start

You can fetch data querying a source name or its coordinates.

```python
from sedbuilder import get_data

# By coordinates
response = get_data(ra=244.9795, dec=-15.64022)
# By name
response = get_data(name="Sco X-1")

# Access data in different formats
table = response.to_astropy()     # Astropy Table
data_dict = response.to_dict()    # Python dictionary
jt = response.to_jetset(z=0.034)  # Jetset table
json_str = response.to_json()     # JSON string
df = response.to_pandas()         # Pandas DataFrame (requires pandas)

# Gets references to the dataset catalog and papers
refs = response.sources()
```

When calling `get_data` by name, `resolve_name` queries the SSDC server — which checks SSDC, SIMBAD, and NED — falling back to the CDS Sesame resolver via astropy if no match is found.

```python
from sedbuilder import resolve_name

(ra, dec), db = resolve_name("Crab Nebula")
```

Resolving a source name takes time. We suggest querying on coordinates when available.


## Development

```bash
# install with development dependencies
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
# routes queries to test server (requires internal network)
source dev.env 
# install linter pre-commit hooks
pre-commit install
# runs tests
pytest
# runs smoke tests against the live server
pytest --smoke
# serve and build documentation
mkdocs serve
mkdocs build
```

For more, see [documentation](https://peppedilillo.github.io/sedbuilder/development/).

## Requests

Need a new feature? Don't hesitate to ask in our [discussion section](https://github.com/peppedilillo/sedbuilder/discussions).


## Documentation

Check out our [API reference](https://peppedilillo.github.io/sedbuilder/api/).
