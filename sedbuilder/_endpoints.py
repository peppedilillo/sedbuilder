"""API endpoint definitions for the SSDC SED Builder service.

This module contains the base URL and endpoint path builders for
the supported endpoints of the ASI-SSDC SED Builder REST API.
"""

from enum import Enum
from typing import Callable

BASE_URL = r"https://tools.ssdc.asi.it/SED-REST/rest"
"""Base URL for the SSDC SED Builder REST API."""


def _get_data(*, ra: float, dec: float) -> str:
    """Build the getData endpoint URL.

    Args:
        ra: Right ascension in degrees.
        dec: Declination in degrees.

    Returns:
        Complete URL for the getData endpoint.
    """
    return f"{BASE_URL}/getData/{ra}/{dec}"


class APIPaths(Enum):
    """Enumeration of available API endpoints.

    Each member stores a callable that builds the complete URL for
    the corresponding API endpoint.
    """

    GET_DATA: Callable = _get_data
    CATALOGS: Callable = lambda: f"{BASE_URL}/catalogs"

    def __call__(self, *args, **kwargs):
        """Make enum members callable by delegating to their value."""
        return self.value(*args, **kwargs)
