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
        Field(description="Path to .json file."),
    ]
):
    return Response.model_validate_json(Path(filepath).read_text())
