"""HTTP request functions for the SSDC SED Builder API.

This module provides functions to interact with the ASI-SSDC SED Builder
REST API endpoints.
"""

from typing import Annotated, Union

import httpx
from pydantic import Field
from pydantic import validate_call

from ._endpoints import APIPaths
from .schemas import CatalogsResponse
from .schemas import GetDataResponse


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


@validate_call
def get_data(
    ra: Annotated[
        float,
        Field(ge=0.0, lt=360.0, description="Right ascension in degrees."),
    ],
    dec: Annotated[
        float,
        Field(ge=-90.0, le=90.0, description="Declination in degrees."),
    ],
    timeout: Annotated[
        Union[float, int],  # TODO: replace with | syntax when we drop python 3.10 support
        Field(gt=0.0, description="Request timeout in seconds."),
    ] = 30.0,
) -> GetDataResponse:
    """Queries the SSDC SED Builder API to retrieve Spectral Energy Distribution
    data for the specified sky coordinates.

    Args:
        ra: Right ascension in degrees (0 to 360).
        dec: Declination in degrees (-90 to 90).
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        A response object. Use its methods to recover data in different formats.

    Raises:
        ValidationError: If coordinates are out of valid range.
        TimeoutError: If the API request exceeds the timeout.
        RuntimeError: If the API request fails for other reasons.

    Example:
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
    """
    r = _get_and_validate(APIPaths.GET_DATA(ra=ra, dec=dec), timeout)
    return GetDataResponse(**r.json())


@validate_call
def catalogs(
    timeout: Annotated[
        Union[float, int],  # TODO: replace with | syntax when we drop python 3.10 support
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
