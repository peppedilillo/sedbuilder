"""HTTP request functions for the SSDC SED Builder API.

This module provides functions to interact with the ASI-SSDC SED Builder
REST API endpoints.
"""

from typing import Annotated

import httpx
from pydantic import Field
from pydantic import validate_call

from ._endpoints import APIPaths
from ._schemas import SEDResponse


@validate_call
def get_data(
    ra: Annotated[float, Field(ge=0.0, lt=360.0, description="Right ascension in degrees.")],
    dec: Annotated[float, Field(ge=-90.0, le=90.0, description="Declination in degrees.")],
) -> SEDResponse:
    """Retrieve SED data for astronomical coordinates.

    Queries the SSDC SED Builder API to retrieve Spectral Energy Distribution
    data for the specified sky coordinates.

    Args:
        ra: Right ascension in degrees (0 to 360).
        dec: Declination in degrees (-90 to 90).

    Returns:
        Dictionary containing the SED data from the API response.

    Raises:
        ValidationError: If coordinates are out of valid range.
        httpx.HTTPError: If the HTTP request fails.

    Example:
        > data = get_data(ra=194.04625, dec=-5.789167)
    """
    r = httpx.get(APIPaths.GET_DATA(ra=ra, dec=dec))
    return SEDResponse(**r.json())
