"""HTTP request functions for the SSDC SED Builder API.

This module provides functions to interact with the ASI-SSDC SED Builder
REST API endpoints.
"""

from typing import Annotated, Union

import httpx
from pydantic import Field
from pydantic import validate_call

from ._endpoints import APIPaths
from .schemas import Response


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
) -> Response:
    """Queries the SSDC SED Builder API to retrieve Spectral Energy Distribution
    data for the specified sky coordinates.

    Args:
        ra: Right ascension in degrees (0 to 360).
        dec: Declination in degrees (-90 to 90).
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        A response object. You can use its methods to recover data in different
        formats, e.g. astropy table, dictionary, json.

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
    try:
        r = httpx.get(APIPaths.GET_DATA(ra=ra, dec=dec), timeout=timeout)
        r.raise_for_status()
    except httpx.ReadTimeout as _:
        raise TimeoutError(f"API request timed out after {timeout}s. Try increasing the timeout parameter.")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"API request failed with status code {e.response.status_code}.")
    except httpx.RequestError as e:
        raise RuntimeError(f"A connectivity error occurred while requesting {e.request.url!r}.")

    return Response(**r.json())


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
