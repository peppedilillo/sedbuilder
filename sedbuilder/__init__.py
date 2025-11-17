"""sedbuilder - Python client for the ASI-SSDC SED Builder API.

This package provides a Python interface to the ASI Space Science Data
Center's SED Builder REST API for retrieving and working with Spectral
Energy Distribution data.

The SSDC SED Builder combines data from several missions and experiments,
both ground and space-based, together with catalogs and archival data.
"""

from sedbuilder.requests import get_data

__all__ = ["get_data"]
