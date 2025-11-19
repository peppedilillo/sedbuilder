from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic import FilePath
from pydantic import validate_call

from .schemas import Response


@validate_call
def get_data_from_json(
    filepath: Annotated[
        FilePath,
        Field(description="Path to JSON file."),
    ]
) -> Response:
    """Load SED data from a JSON file.

    Reads a JSON file containing SED Builder API response data and validates it
    against `get_data` response schema.

    Args:
        filepath: Path to a JSON file containing SED Builder response data.
            The file must exist and contain valid JSON matching the `get_data`
            response schema.

    Returns:
        Response object with validated SED data.

    Raises:
        ValidationError: If the file does not exists, or if file content does not
         match the expected response schema.

    Example:
        ```python
        from sedbuilder import get_data_from_json

        # Load SED data from a saved JSON file
        response = get_data_from_json("path/to/sed_data.json")

        # Convert to Astropy Table
        table = response.to_astropy()
        ```
    """
    return Response.model_validate_json(Path(filepath).read_text())
