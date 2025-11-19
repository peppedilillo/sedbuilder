# sedbuilder

The **sedbuilder** package provides a Python interface to the ASI Space Science Data Center's SED Builder REST API for retrieving Spectral Energy Distribution data for astronomical sources.

> NOTE
> At present, `sedbuilder` is only internally operational. 
> This means you must need to be on the ASI-SSDC network to use it.
> We will release to public soon.

## Overview

The [SED Builder](https://tools.ssdc.asi.it/SED/) is a web-based program developed at the ASI-SSDC to produce and display the Spectral Energy Distribution (SED) of astrophysical sources. The tool combines data from several missions and experiments, both ground and space-based, together with catalogs and archival data.

At present, only internally hosted catalogs are supported. Don't hesitate to ask for any new feature in our discussion section.

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
table = response.to_astropy()    # Astropy Table
data_dict = response.to_dict()   # Python dictionary
jetset = response.to_jetset()  # Jetset
json_str = response.to_json()    # JSON string
df = response.to_pandas()        # Pandas DataFrame (requires pandas)
```

## Development

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev]"
pre-commit install
pytest
```

## Documentation

Full documentation available at: ..
