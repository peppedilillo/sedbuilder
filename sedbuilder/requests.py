"""HTTP request functions for the SSDC SED Builder API.

This module provides functions to interact with the ASI-SSDC SED Builder
REST API endpoints.
"""

import logging
from typing import Annotated, Never, overload, Sequence

import httpx
from pydantic import Field
from pydantic import validate_call

from ._endpoints import APIPaths
from .schemas import CatalogsResponse
from .schemas import GetDataResponse
from .schemas import NameResolverResponse

_log = logging.getLogger(__name__)


def _get_and_validate(url: str, timeout: float) -> httpx.Response:
    """Make HTTP request and handle errors.

    Args:
        url: The URL to request.
        timeout: Request timeout in seconds.

    Returns:
        The validated HTTP response.

    Raises:
        TimeoutError: If the request times out.
        RuntimeError: If the request fails for other reasons.
    """
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except httpx.ReadTimeout:
        raise TimeoutError(f"API request timed out after {timeout}s. Try increasing the timeout parameter.")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"API request failed with status code {e.response.status_code}.")
    except httpx.RequestError as e:
        raise RuntimeError(f"A connectivity error occurred while requesting {e.request.url!r}.")


_DB_PRIORITY = {"SSDC": 0, "SIMBAD": 1, "NED": 2}


def _resolve_name_astropy(name: str) -> tuple[float, float] | None:
    """Resolve a source name to (ra, dec) using astropy's CDS/Sesame resolver.

    Args:
        name: Source name to resolve.

    Returns:
        A ``(ra, dec)`` tuple in degrees, or ``None`` if the name is not found.
    """
    from astropy.coordinates import SkyCoord
    from astropy.coordinates.name_resolve import NameResolveError

    try:
        coord = SkyCoord.from_name(name)
    except NameResolveError:
        return None
    return coord.ra.deg, coord.dec.deg


@validate_call
def resolve_name(
    name: str,
    timeout: Annotated[float, Field(gt=0.0)] = 2.0,
) -> tuple[tuple[float, float], str]:
    """Resolve a source name to (ra, dec) via SSDC name resolver, with astropy fallback.

    Queries the SSDC server — which checks SSDC, SIMBAD, and NED — falling back to the CDS Sesame resolver via astropy if no match is found.

    Args:
        name: Source name to resolve.
        timeout: Timeout in seconds for the SSDC request. Defaults to 2.0.

    Returns:
        The source `(ra, dec)` tuple, in degrees.
        `str` containing the name of the DB resolving the call.

    Raises:
        RuntimeError: If no resolver can identify the source.

    Example:
        ```python
        from sedbuilder import resolve_name

        (ra, dec), db = resolve_name("Crab Nebula")
        ```
    """
    try:
        r = _get_and_validate(APIPaths.NAME_RESOLVER(name=name, ssdc=True, simbad=True, ned=True), timeout)
        response = NameResolverResponse(**r.json())
    except (TimeoutError, RuntimeError):
        response = NameResolverResponse(results=[])
    if response.results:
        item = min(response.results, key=lambda item: _DB_PRIORITY[item.db])
        ra, dec = item.ra, item.dec
        source = item.db
    else:
        coords = _resolve_name_astropy(name)
        if coords is None:
            raise RuntimeError(f"Cannot resolve source {name!r}.")
        ra, dec = coords
        source = "astropy"
    _log.info("Resolved %r → ra=%.6f, dec=%.6f (via %s)", name, ra, dec, source)
    return (ra, dec), source


@validate_call
def _get_data_coords(
    ra: Annotated[float, Field(ge=0.0, lt=360.0)],
    dec: Annotated[float, Field(ge=-90.0, le=90.0)],
    catalog_ids: Sequence[int] = tuple(),
    timeout: Annotated[
        float | int,
        Field(gt=0.0),
    ] = 30.0,
) -> GetDataResponse:
    """Fetch SED data for validated sky coordinates.

    Args:
        ra: Right ascension in degrees, must be in [0, 360).
        dec: Declination in degrees, must be in [-90, 90].
        catalog_ids:  A sequence of catalog ids to query from.
        timeout: Request timeout in seconds.

    Returns:
        Validated API response.

    Raises:
        ValidationError: If coordinates are out of range.
        TimeoutError: If the request times out.
        RuntimeError: If the request fails.
    """
    r = _get_and_validate(APIPaths.GET_DATA(ra=ra, dec=dec, catalog_ids=catalog_ids), timeout)
    return GetDataResponse(**r.json())


@overload
def get_data(
    *args: Never,
    ra: float,
    dec: float,
    catalog_ids: Sequence[int] = tuple(),
    timeout: float = ...,
) -> GetDataResponse: ...
@overload
def get_data(
    *args: Never,
    name: str,
    catalog_ids: Sequence[int] = tuple(),
    timeout: float = ...,
) -> GetDataResponse: ...


def get_data(
    *args,
    name: str = None,
    ra: float = None,
    dec: float = None,
    catalog_ids: Sequence[int] = tuple(),
    timeout: float = 30.0,
) -> GetDataResponse:
    """Queries the SSDC SED Builder API to retrieve Spectral Energy Distribution
    data for the specified sky coordinates or source name.

    Args:
        ra: Right ascension in degrees (0 to 360). Mutually exclusive with `name`.
        dec: Declination in degrees (-90 to 90). Mutually exclusive with `name`.
        name: Source name to resolve to coordinates. Tried against SSDC, SIMBAD,
            NED, and finally astropy's CDS/Sesame resolver.
        catalog_ids: A sequence of catalog ids to query from (see Notes).
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        A response object. Use its methods to recover data in different formats.

    Raises:
        ValueError: If arguments are invalid or conflicting.
        ValidationError: If coordinates are out of valid range.
        TimeoutError: If the API request exceeds the timeout.
        RuntimeError: If the API request fails for other reasons.

    Example:
        ```python
        from sedbuilder import get_data

        # By coordinates
        response = get_data(ra=194.04625, dec=-5.789167)
        # By name
        response = get_data(name="Crab Nebula")

        # Access data in different formats
        table = response.to_astropy()     # Astropy Table
        data_dict = response.to_dict()    # Python dictionary
        jt = response.to_jetset(z=0.034)  # Jetset table
        json_str = response.to_json()     # JSON string
        df = response.to_pandas()         # Pandas DataFrame (requires pandas)
        ```

    Note:
        You can find available catalogs and their ids with [`catalogs`][sedbuilder.requests.catalogs].
    """
    if args:
        raise TypeError(
            "Are you trying to call `get_data` with a positional argument? "
            "get_data() accepts keyword arguments only. "
            f"Hint: get_data(name='Crab Nebula'); get_data(ra=194.04, dec=-5.78)."
        )
    if name is not None and ((ra is None) and (dec is None)):
        # we are calling _resolve_name leaving its default timeout
        # this is to avoid waiting too long for just the name resolver
        # if we get delayed by the exponential rate meter
        (ra, dec), _ = resolve_name(name)
        return _get_data_coords(ra=ra, dec=dec, catalog_ids=catalog_ids, timeout=timeout)
    if name is None and ((ra is not None) and (dec is not None)):
        return _get_data_coords(ra=ra, dec=dec, catalog_ids=catalog_ids, timeout=timeout)
    # catches missing args, partial coordinates or mixed name/coordinates queries
    raise ValueError("Provide either 'name' or both 'ra' and 'dec'.")


@validate_call
def catalogs(
    timeout: Annotated[
        float | int,
        Field(gt=0.0, description="Request timeout in seconds."),
    ] = 30.0,
) -> CatalogsResponse:
    """Queries the SSDC SED Builder API to retrieve the list of available catalogs.

    Args:
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        A response object containing catalog information. Use its methods to recover data in different formats.

    Raises:
        TimeoutError: If the API request exceeds the timeout.
        RuntimeError: If the API request fails for other reasons.

    Example:
        ```python
        from sedbuilder import catalogs

        # Get list of available catalogs
        response = catalogs()

        # Access catalog data as a list of dictionaries
        catalog_list = response.to_list()
        ```
    """
    r = _get_and_validate(APIPaths.CATALOGS(), timeout)
    return CatalogsResponse(**r.json())


"""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣷⣮⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣻⣿⣿⣿⣿⣿⠂⠀⠀
⠀⠀⠀⠀⠀⠀⣠⣿⣿⣿⣿⣿⠋⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⢸⣧⠁⠀⠀⠀
⠀⡀⠀⠀⠀⠀⢸⣿⣿⣿⣸⣿⣷⣄⠀⠀
⠀⠈⠫⠂⠀⠀⠊⣿⢿⣿⡏⣿⠿⠟⠀⠀
⠀⠀⠀⠀⠱⡀⠈⠁⠀⢝⢷⡸⡇⠀⠀⠀
⠀⠀⠀⠀⢀⠇⠀⠀⢀⣾⣦⢳⡀⠀⠀⠀
⠀⠀⠀⢀⠎⠀⢀⣴⣿⣿⣿⡇⣧⠀⠀⠀
⠀⢀⡔⠁⠀⢠⡟⢻⡻⣿⣿⣿⣌⡀⠀⠀
⢀⡎⠀⠀⠀⣼⠁⣼⣿⣦⠻⣿⣿⣷⡀⠀
⢸⠀⠀⠀⠀⡟⢰⣿⣿⡟⠀⠘⢿⣿⣷⡀
⠈⠳⠦⠴⠞⠀⢸⣿⣿⠁⠀⠀⠀⠹⣿⡧
⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⢰⣿⡇
⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⢸⣿⡇
⠀⠀⠀⠀⠀⡀⢸⣿⠁⠀⠀⠀⠀⢸⣿⡇
⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⣿⡇
⠀⠀⠀⠀⠀⠀⠀⣿⣆⠀⠀⠀⠀⠀⣿⣧
⠀⠀⠀⠀⠀⠀⠀⠏⢿⠄⠀⠀⠀⠐⢸⣿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉
"""
