# sedbuilder

The **sedbuilder** package implements a Python interface to the ASI Space Science Data Center's SED Builder REST API.

## Overview

This package provides programmatic access to multi-wavelength spectral energy distribution (SED) data from catalogs, surveys, and archival observations across the electromagnetic spectrum.
It is based on [SED Builder](https://tools.ssdc.asi.it/SED/), a software developed at the ASI-SSDC to produce and display the SED data over the web.

## Installation

```bash
pip install sedbuilder
```

## Quick Start

```python
from sedbuilder import get_data

# Get response from SED for astronomical coordinates
response = get_data(ra=194.04625, dec=-5.789167)

# Access data in different formats
table = response.to_astropy()     # Astropy Table
data_dict = response.to_dict()    # Python dictionary
jt = response.to_jetset(z=0.034)  # Jetset table
json_str = response.to_json()     # JSON string
df = response.to_pandas()         # Pandas DataFrame (requires pandas)
```

## Development

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
pre-commit install
pytest
```

## Requests

Need a new feature? Don't hesitate to ask in our [discussion section](https://github.com/peppedilillo/sedbuilder/discussions).


## Documentation

Check out our [documentation](https://peppedilillo.github.io/sedbuilder/).
