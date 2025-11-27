from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic import FilePath
from pydantic import validate_call

from .schemas import CatalogsResponse
from .schemas import GetDataResponse


@validate_call
def get_data_from_json(
    filepath: Annotated[
        FilePath,
        Field(description="Path to JSON file."),
    ],
) -> GetDataResponse:
    """Reads a JSON file containing SED Builder API response data and validates it
    against `get_data` response schema.

    Args:
        filepath: Path to a JSON file containing SED Builder response data.
                  The file must exist and contain valid JSON matching the `get_data`
                  response schema.

    Returns:
        Response object with validated SED data.

    Raises:
        ValidationError: If the file does not exist, or if file content does not
                         match the expected response schema.
    """
    return GetDataResponse.model_validate_json(Path(filepath).read_text())


@validate_call
def catalogs_from_json(
    filepath: Annotated[
        FilePath,
        Field(description="Path to JSON file."),
    ],
) -> CatalogsResponse:
    """Reads a JSON file containing SED Builder API catalog data and validates it
    against `catalogs` response schema.

    Args:
        filepath: Path to a JSON file containing SED Builder catalog data.
                  The file must exist and contain valid JSON matching the `catalogs`
                  response schema.

    Returns:
        Response object with validated catalog information.

    Raises:
        ValidationError: If the file does not exist, or if file content does not
                         match the expected response schema.
    """
    return CatalogsResponse.model_validate_json(Path(filepath).read_text())
