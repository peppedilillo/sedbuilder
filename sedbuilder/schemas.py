"""Pydantic models for validating SSDC SED Builder API responses.

This module defines the schema for the JSON responses returned by the
SED Builder API, providing validation and type safety.
"""

import json
from typing import Annotated, Literal, Optional

from astropy.table import Table
import astropy.units as u
from pydantic import BaseModel
from pydantic import Field
from pydantic import validate_call


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

    Nh: Annotated[
        float,
        Field(ge=0.0, description="Hydrogen column density in cm^-2."),
    ]


class Catalog(BaseModel):
    """Catalog metadata.

    Attributes:
        CatalogName: Name of the astronomical catalog.
        ErrorRadius: Search radius in arcsec used for source matching.
    """

    CatalogName: str
    ErrorRadius: Annotated[
        float,
        Field(ge=0.0, description="Error radius in arcsec."),
    ]


class SourceData(BaseModel):
    """Spectral energy distribution data point.

    This model represents a single row from a catalog.
    """

    Frequency: Annotated[
        float,
        Field(gt=0.0, description="Frequency of the observation in Hz."),
    ]
    Nufnu: Annotated[
        float,
        Field(description="Spectral flux density (nu*F_nu) in erg/cm^2/s."),
    ]
    FrequencyError: Annotated[
        float,
        Field(ge=0.0, description="Error on frequency in Hz."),
    ]
    NufnuError: Annotated[
        float,
        Field(description="Error on spectral flux density in erg/cm^2/s."),
    ]
    Name: Annotated[
        Optional[str],
        Field(default=None, description="Optional source name in the catalog."),
    ]
    AngularDistance: Annotated[
        Optional[float],
        Field(default=None, ge=0.0, description="Angular distance from query position in arcsec."),
    ]
    StartTime: Annotated[
        Optional[float],
        Field(default=None, ge=0.0, description="Start time of observation in MJD."),
    ]
    StopTime: Annotated[
        Optional[float],
        Field(default=None, ge=0.0, description="End time of observation in MJD."),
    ]
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
        str,
        Field(default=None, description="Optional information flag (e.g., 'Upper Limit', quality notes)."),
    ]


class CatalogEntry(BaseModel):
    """A catalog entry with its associated source data.

    Attributes:
        Catalog: Metadata about the catalog.
        SourceData: List of measurements from this catalog.
    """

    Catalog: Catalog
    SourceData: list[SourceData | UpperLimits]


MAP_COLUMN_UNIT = {
    "Frequency": u.Hz,
    "Nufnu": u.erg / (u.cm**2 * u.s),
    "FrequencyError": u.Hz,
    "NufnuError": u.erg / (u.cm**2 * u.s),
    "AngularDistance": u.arcsec,
    "StartTime": u.d,
    "StopTime": u.d,
    "ErrorRadius": u.arcsec,
    "Nh": u.cm**-2,
}


class Response(BaseModel):
    """Complete SED Builder API response.

    To retrieve data you call `.to_astropy()`, or `.to_dict()` and other methods.

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

    def to_dict(self) -> dict:
        """
        Converts data to a dictionary.

        Returns:
            A dictionary from the response JSON.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """
        Converts data to JSON.

        Returns:
            A JSON string.
        """
        return json.dumps(self.model_dump())

    def to_pandas(self):
        """
        Converts data to a pandas DataFrame.

        Requires pandas to be installed. Install with:
            pip install pandas

        Returns:
            A pandas dataframe.

        Raises:
            ImportError: If pandas is not installed.
        """
        try:
            return self.to_astropy().to_pandas()
        except AttributeError:
            raise ImportError("pandas is required for this method. Install it with: pip install pandas")

    def to_astropy(self) -> Table:
        """Convert data to an astropy Table.

        Returns:
            Astropy Table with one row per SourceData entry, including catalog column.
            Columns have appropriate physical units assigned. Hydrogen column is added
            to the table's metadata.
        """
        rows = []

        for catalog_entry in self.Catalogs:
            for source_data in catalog_entry.SourceData:
                # TODO: remove once API is fixed to return data for warning-tagged rows
                if not isinstance(source_data, SourceData):
                    continue

                row = {
                    **source_data.model_dump(),
                    "Catalog": catalog_entry.Catalog.CatalogName,
                    "ErrorRadius": catalog_entry.Catalog.ErrorRadius,
                }
                rows.append(row)

        table = Table(rows=rows)
        for column in table.columns:
            if column in MAP_COLUMN_UNIT:
                table[column].unit = MAP_COLUMN_UNIT[column]
        table.meta["Nh"] = self.Properties.Nh * MAP_COLUMN_UNIT["Nh"]
        return table

    @validate_call
    def to_jetset(
        self,
        z: Annotated[
            float,
            Field(ge=0.0, le=1.0, description="Source redshift, must be between 0 and 1."),
        ],
        ul_cl: Annotated[
            float,
            Field(ge=0.0, le=1.0, description="Confidence level for upper limits,must be between 0 and 1."),
        ] = 0.95,
        restframe: Annotated[
            Literal["obs", "src"],
            Field(description="Reference frame for the data. Defaults to 'obs'."),
        ] = "obs",
        data_scale: Annotated[
            Literal["lin-lin", "log-log"],
            Field(description="Scale format of the data."),
        ] = "lin-lin",
        obj_name: Annotated[
            str,
            Field(description="Name identifier for the object."),
        ] = "new-src",
    ) -> dict:
        # noinspection PyUnresolvedReferences
        """Convert SED data t   able to Jetset format.

        The output includes both the data table with renamed columns and appropriate units,
        plus metadata needed for Jetset analysis.

        Args:
            z: Source redshift, must be between 0 and 1,
            ul_cl: Confidence level for upper limits,must be between 0 and 1,
                exclusive. Default is 0.95.
            restframe: Reference frame for the data. Options are "obs" for observed flux (default)
                and "src" for source luminosities.
            data_scale: Scale format of the data. Options are  "lin-lin" for linear scale (default),
                and "log-log" for logarithmic scale.
            obj_name: Name identifier for the object. Default is "new-src".

        Returns:
            Dictionary with two keys:
                - "data_table": Astropy Table with Jetset column names and units.
                - "meta_data": Dictionary containing Jetset metadata.

        Raises:
            ValueError: If z < 0, ul_cl is not in (0, 1), restframe or data_scale
                have invalid values, obj_name is empty, or required table columns
                are missing.

        Example:
            ```python
            from sedbuilder import get_data
            from jetset_data.data_loader import Data

            # Get response from SED for astronomical coordinates
            response = get_data(ra=194.04625, dec=-5.789167)
            # Initialize jetset data structure
            jetset_data = Data(**response.to_jetset(z=0.034))
            ```
        """
        map_column_jetset = {
            "Frequency": "x",
            "Nufnu": "y",
            "FrequencyError": "dx",
            "NufnuError": "dy",
            "StartTime": "T_start",
            "StopTime": "T_stop",
            "Catalog": "data_set",
        }
        table = self.to_astropy()
        missing_columns = [*filter(lambda x: x not in table.colnames, map_column_jetset.keys())]
        if any(missing_columns):
            raise ValueError(f"Table missing required columns: {', '.join(missing_columns)}")

        jetset_table = Table()
        for col_label, col_label_jetset in map_column_jetset.items():
            jetset_table.add_column(table[col_label], name=col_label_jetset)
            if col_label in MAP_COLUMN_UNIT:
                jetset_table[col_label_jetset].unit = MAP_COLUMN_UNIT[col_label]

        return {
            "data_table": jetset_table,
            "meta_data": {
                "z": z,
                "UL_CL": ul_cl,
                "restframe": restframe,
                "data_scale": data_scale,
                "obj_name": obj_name,
            },
        }
