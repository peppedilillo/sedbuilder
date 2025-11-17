"""Pydantic models for validating SSDC SED Builder API responses.

This module defines the schema for the JSON responses returned by the
SED Builder API, providing validation and type safety.
"""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel
from pydantic import Field


class ResponseInfo(BaseModel):
    """Response status information.

    Attributes:
        statusCode: Status code of the response (e.g., 'OK', 'ERROR').
        message: Optional message with additional information.
    """

    statusCode: str
    message: Optional[str] = None


class Properties(BaseModel):
    """Additional properties for the queried source.

    Attributes:
        Nh: Hydrogen column density in cm^-2 along the line of sight.
    """

    Nh: Annotated[float, Field(ge=0.0, description="Hydrogen column density in cm^-2.")]


class Catalog(BaseModel):
    """Catalog metadata.

    Attributes:
        CatalogName: Name of the astronomical catalog.
        ErrorRadius: Search radius in arcsec used for source matching.
    """

    CatalogName: str
    ErrorRadius: Annotated[float, Field(ge=0.0, description="Error radius in arcsec.")]


class SourceData(BaseModel):
    """Spectral energy distribution data point.

    This model represents a single row from a catalog.
    """

    Frequency: Annotated[float, Field(gt=0.0, description="Frequency of the observation in Hz.")]
    Nufnu: Annotated[float, Field(description="Spectral flux density (nu*F_nu) in erg/cm^2/s.")]
    FrequencyError: Annotated[float, Field(ge=0.0, description="Error on frequency in Hz.")]
    NufnuError: Annotated[float, Field(description="Error on spectral flux density in erg/cm^2/s.")]
    Name: Annotated[Optional[str], Field(default=None, description="Optional source name in the catalog.")]
    AngularDistance: Annotated[
        Optional[float], Field(default=None, ge=0.0, description="Angular distance from query position in arcsec.")
    ]
    StartTime: Annotated[Optional[float], Field(default=None, ge=0.0, description="Start time of observation in MJD.")]
    StopTime: Annotated[Optional[float], Field(default=None, ge=0.0, description="End time of observation in MJD.")]
    Info: Annotated[
        Optional[str],
        Field(default=None, description="Optional information flag (e.g., 'Upper Limit', quality notes)."),
    ]


class UpperLimits(BaseModel):
    """At present, the get_data API cuts out data from measurements with warning error.
    We have to parse these separately for the moment, but will be later removed once the schema is fixed.

    TODO: Ask Fabrizio to not drop data from entries tagged with warnings, then remove and update `CatalogEntry`.
    """

    Info: Annotated[
        str, Field(default=None, description="Optional information flag (e.g., 'Upper Limit', quality notes).")
    ]


class CatalogEntry(BaseModel):
    """A catalog entry with its associated source data.

    Attributes:
        Catalog: Metadata about the catalog.
        SourceData: List of measurements from this catalog.
    """

    Catalog: Catalog
    SourceData: list[SourceData | UpperLimits]


class SEDResponse(BaseModel):
    """Complete SED Builder API response.

    This is the root model for validating the entire API response.

    Attributes:
        ResponseInfo: Status information about the API response.
        Properties: Additional properties for the queried source.
        Catalogs: List of catalog entries with measurements.
    """

    ResponseInfo: ResponseInfo
    Properties: Properties
    Catalogs: list[CatalogEntry]

    def is_successful(self) -> bool:
        """Check if the API response indicates success.

        Returns:
            True if the response status code is 'OK'.
        """
        return self.ResponseInfo.statusCode == "OK"
