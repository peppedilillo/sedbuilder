"""Pydantic models for validating SSDC SED Builder API responses.

This module defines the schema for the JSON responses returned by the
SED Builder API, providing validation and type safety.
"""

from dataclasses import dataclass
import json
from typing import Annotated, Literal, NamedTuple, Optional

from astropy.table import hstack
from astropy.table import Table
import astropy.units as u
import numpy as np
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
        Field(default="", description="Optional source name in the catalog."),
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
        Field(default="", description="Optional information flag (e.g., 'Upper Limit', quality notes)."),
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


class DataColumn(NamedTuple):
    name: str  # field name in SourceData
    dtype: type
    units: u.Unit | None


class CatalogColumn(NamedTuple):
    name: str  # field name in Catalog
    dtype: type
    units: u.Unit | None


class PropertyMetadata(NamedTuple):
    name: str  # field name in Properties
    units: u.Unit | None


@dataclass(frozen=True)
class AstropySchema:
    NAME = DataColumn("Name", str, None)
    FREQUENCY = DataColumn("Frequency", np.float64, u.Hz)
    NUFNU = DataColumn("Nufnu", np.float64, u.erg / (u.cm**2 * u.s))
    FREQUENCY_ERROR = DataColumn("FrequencyError", np.float64, u.Hz)
    NUFNU_ERROR = DataColumn("NufnuError", np.float64, u.erg / (u.cm**2 * u.s))
    ANGULAR_DISTANCE = DataColumn("AngularDistance", np.float64, u.arcsec)
    START_TIME = DataColumn("StartTime", np.float64, u.d)
    STOP_TIME = DataColumn("StopTime", np.float64, u.d)
    INFO = DataColumn("Info", str, None)
    CATALOG = CatalogColumn("CatalogName", str, None)
    ERROR_RADIUS = CatalogColumn("ErrorRadius", np.float64, u.arcsec)
    METADATA_NH = PropertyMetadata("Nh", u.cm**-2)

    def columns(self, kind: Literal["data", "catalog", "all"] = "all"):
        """Iterate over columns, defines table order."""
        if kind == "all" or kind == "data":
            yield self.NAME
            yield self.FREQUENCY
            yield self.NUFNU
            yield self.FREQUENCY_ERROR
            yield self.NUFNU_ERROR
            yield self.ANGULAR_DISTANCE
            yield self.START_TIME
            yield self.STOP_TIME
            yield self.INFO
        if kind == "all" or kind == "catalog":
            yield self.CATALOG
            yield self.ERROR_RADIUS

    def metadata(self):
        """Iterate over metadata, defines table order."""
        yield self.METADATA_NH


TABLE_SCHEMA = AstropySchema()


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
        # we build two different tables one for the data columns and one for the catalog columns.
        # then, we stack them horizontally
        rows_data, rows_catalog = [], []
        for catalog_entry in self.Catalogs:
            catalog_dump = catalog_entry.Catalog.model_dump()
            for source_data in catalog_entry.SourceData:
                if not isinstance(source_data, SourceData):
                    continue
                rows_data.append(source_data.model_dump())
                rows_catalog.append(catalog_dump)

        # first, the column table
        columns_data = [*TABLE_SCHEMA.columns(kind="data")]
        table_data = Table(
            rows_data,
            names=[col.name for col in columns_data],
            dtype=[col.dtype for col in columns_data],
            units=[col.units for col in columns_data],
        )

        # second, the catalog property table
        columns_catalog = [*TABLE_SCHEMA.columns(kind="catalog")]
        table_catalog = Table(
            rows_catalog,
            names=[col.name for col in columns_catalog],
            dtype=[col.dtype for col in columns_catalog],
            units=[col.units for col in columns_catalog],
        )
        # finally, we stack
        table = hstack((table_data, table_catalog))
        # and add metadata
        for m in TABLE_SCHEMA.metadata():
            table.meta[m.name] = getattr(self.Properties, m.name)
            if m.units:
                table.meta[m.name] *= m.units
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
    ) -> Table:
        # noinspection PyUnresolvedReferences
        """Convert SED data to Jetset format.

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
            A table with column names, units and metadata, compatible with `jetset.data_loader.Data`.

        Raises:
            ValueError: If z < 0, ul_cl is not in (0, 1), restframe or data_scale
                have invalid values, obj_name is empty, or required table columns
                are missing.

        Example:
            ```python
            from sedbuilder import get_data
            from jetset.data_loader import Data

            # Get response from SED for astronomical coordinates
            response = get_data(ra=194.04625, dec=-5.789167)
            # Initialize jetset data structure
            jetset_data = Data(response.to_jetset(z=0.034))
            ```
        """
        # type and label choice from Jetset documentation, "Data format and SED data".
        t = self.to_astropy()
        table = Table()
        table.add_column(t[TABLE_SCHEMA.FREQUENCY.name].astype(np.float64), name="x")
        table.add_column(t[TABLE_SCHEMA.FREQUENCY_ERROR.name].astype(np.float64), name="dx")
        table.add_column(t[TABLE_SCHEMA.NUFNU.name].astype(np.float64), name="y")
        table.add_column(t[TABLE_SCHEMA.NUFNU_ERROR.name].astype(np.float64), name="dy")
        table.add_column(
            np.nan_to_num(t[TABLE_SCHEMA.START_TIME.name].value, nan=0.0).astype(np.float64), name="T_start"
        )
        table.add_column(np.nan_to_num(t[TABLE_SCHEMA.STOP_TIME.name].value, nan=0.0).astype(np.float64), name="T_stop")
        # TODO: fix this once we have proper warning/info
        table.add_column(np.zeros(len(t), dtype=bool), name="UL")
        table.add_column(t[TABLE_SCHEMA.CATALOG.name].astype(str), name="dataset")
        table.meta["z"] = z
        table.meta["UL_CL"] = ul_cl
        table.meta["restframe"] = restframe
        table.meta["data_scale"] = data_scale
        table.meta["obj_name"] = obj_name
        return table
