"""API endpoint definitions for the SSDC SED Builder service.

This module contains the base URL and endpoint path builders for
the supported endpoints of the ASI-SSDC SED Builder REST API.
"""

from enum import Enum
import os
from typing import Callable
from urllib.parse import quote

_DEV_DOMAIN_URL = r"https://toolsdev2.ssdc.asi.it"
"""Nightly URL for the SSDC SED Builder REST API."""
_PROD_DOMAIN_URL = r"https://tools.ssdc.asi.it"
"""Production URL for the SSDC SED Builder REST API."""
_SED_PATH = r"/SED-REST/rest"
DOMAIN_URL = _DEV_DOMAIN_URL if int(os.getenv("SEDBUILDER_DEV", "0")) else _PROD_DOMAIN_URL
SED_URL = f"{DOMAIN_URL}{_SED_PATH}"


def _get_data(*, ra: float, dec: float, catalog_ids: tuple[int] = tuple()) -> str:
    """Build the getData endpoint URL.

    Args:
        ra: Right ascension in degrees.
        dec: Declination in degrees.
        catalog_ids: The ids of the catalogs to fetch.

    Returns:
        Complete URL for the getData endpoint.
    """
    if not catalog_ids:
        return f"{SED_URL}/getData?ra={ra}&dec={dec}"
    catalog_string = "-".join(map(str, catalog_ids))
    return f"{SED_URL}/getData?ra={ra}&dec={dec}&catalogs={catalog_string}"


def _name_resolver(*, name: str, ssdc: bool, simbad: bool, ned: bool) -> str:
    """Build the name resolver endpoint URL.

    Args:
        name: the term to resolve (e.g., 'Crab Nebula')
        ssdc: whether or not to query the ssdc internal name resolver.
        simbad: whether or not to query the simbad name resolver.
        ned: whether or not to query the ned name resolver.

    Returns:
        Complete URL for the nameresolver endpoint.
    """
    return (
        f"{DOMAIN_URL}/"
        "AutoComplete?"
        f"fromSelect2=true&"
        f"term={quote(name)}&"
        f"NameResolverLOCAL={'true' if ssdc else 'false'}&"
        f"NameResolverSIMBAD={'true' if simbad else 'false'}&"
        f"NameResolverNED={'true' if ned else 'false'}"
    )


class APIPaths(Enum):
    """Enumeration of available API endpoints.

    Each member stores a callable that builds the complete URL for
    the corresponding API endpoint.
    """

    GET_DATA: Callable = _get_data
    CATALOGS: Callable = lambda: f"{SED_URL}/catalogs"
    NAME_RESOLVER: Callable = _name_resolver

    def __call__(self, *args, **kwargs):
        """Make enum members callable by delegating to their value."""
        return self.value(*args, **kwargs)
