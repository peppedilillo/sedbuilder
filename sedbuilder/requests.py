"""HTTP request functions for the SSDC SED Builder API.

This module provides functions to interact with the ASI-SSDC SED Builder
REST API endpoints.
"""

from typing import Annotated, Literal

from astropy.table import Table
import httpx
from pydantic import Field
from pydantic import validate_call

from ._endpoints import APIPaths
from ._schemas import SEDResponse


@validate_call
def get_data(
    ra: Annotated[float, Field(ge=0.0, lt=360.0, description="Right ascension in degrees.")],
    dec: Annotated[float, Field(ge=-90.0, le=90.0, description="Declination in degrees.")],
    fmt: Literal["raw", "astropy"] = "astropy",
    timeout: Annotated[float, Field(gt=0.0, description="Request timeout in seconds.")] = 30.0,
) -> dict | Table:
    """Retrieve SED data from astronomical coordinates.

    Queries the SSDC SED Builder API to retrieve Spectral Energy Distribution
    data for the specified sky coordinates.

    Args:
        ra: Right ascension in degrees (0 to 360).
        dec: Declination in degrees (-90 to 90).
        fmt: Output format for the data. Options:
                - "raw": Returns a dictionary from the response JSON.
                - "astropy": Returns an astropy Table with flattened catalog data.
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        If format="raw": Dictionary containing the complete API response.
        If format="astropy": Astropy Table with one row per measurement, including
                            a Catalog column. Upper limit entries are excluded.

    Raises:
        ValidationError: If coordinates are out of valid range.
        TimeoutError: If the API request exceeds the timeout.
        RuntimeError: If the API request fails for other reasons.

    Example:
        >>> # Get data as astropy Table (default)
        >>> table = get_data(ra=194.04625, dec=-5.789167)
        >>> # Get raw JSON response
        >>> data = get_data(ra=194.04625, dec=-5.789167, fmt="raw")
    """
    try:
        r = httpx.get(APIPaths.GET_DATA(ra=ra, dec=dec), timeout=timeout)
        r.raise_for_status()
    except httpx.ReadTimeout as _:
        raise TimeoutError(f"API request timed out after {timeout}s. Try increasing the timeout parameter.")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"API request failed with status code {e.response.status_code}.")
    except httpx.RequestError as e:
        raise RuntimeError(f"An error occurred while requesting {e.request.url!r}.")

    response = SEDResponse(**r.json())

    if fmt == "raw":
        return response.model_dump()
    elif fmt == "astropy":
        return response.to_astropy()
    else:
        raise ValueError(f"Unknown format: {fmt}")
