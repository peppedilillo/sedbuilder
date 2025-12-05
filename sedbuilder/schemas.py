"""Pydantic models for validating SSDC SED Builder API responses.

This module defines the schema for the JSON responses returned by the
SED Builder API, providing validation and type safety.
"""

from dataclasses import dataclass
import json
from typing import Annotated, Any, Literal, NamedTuple, Optional

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
        Optional[float],
        Field(default=None, description="Hydrogen column density in cm^-2."),
    ]
    Units: Annotated[
        dict[str, str],
        Field(default=None, description="Units of measure for data and properties."),
    ]


class Catalog(BaseModel):
    """Catalog metadata.

    Attributes:
        CatalogName: Name of the astronomical catalog.
        CatalogId: Unique identifier for the catalog.
        ErrorRadius: Search radius in arcsec used for source matching.
        CatalogBand: Spectral band classification (e.g., 'Radio', 'Infrared', 'Optical').
    """

    CatalogName: str
    CatalogId: int
    ErrorRadius: Annotated[
        float,
        Field(ge=0.0, description="Error radius in arcsec."),
    ]
    CatalogBand: Annotated[
        Optional[str],
        Field(default=None, description="Catalog spectral classifier."),
    ]

    def __repr__(self) -> str:
        return (
            f"Catalog(CatalogName={self.CatalogName!r}, "
            f"CatalogId={self.CatalogId}, "
            f"ErrorRadius={self.ErrorRadius}, "
            f"CatalogBand={self.CatalogBand!r})"
        )


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
        Field(
            default="",
            description="Optional information flags (e.g., 'Upper Limit', quality notes). Multiple values may be separated by the separator defined in Meta.InfoSeparator.",
        ),
    ]


class Dataset(BaseModel):
    """A catalog entry with its associated source data.

    Attributes:
        Catalog: Metadata about the catalog.
        SourceData: List of measurements from this catalog.
    """

    Catalog: Catalog
    SourceData: list[SourceData]

    def __repr__(self) -> str:
        return f"Dataset({self.Catalog!r}, SourceData: [#{len(self.SourceData)} entries])"


class DataColumn(NamedTuple):
    name: str  # field name in SourceData
    dtype: type
    units: u.Unit | None


class CatalogColumn(NamedTuple):
    name: str  # field name in Catalog
    dtype: type
    units: u.Unit | None

    def __eq__(self, other: str):
        return self.name == other


class PropertyMetadata(NamedTuple):
    name: str  # field name in Properties
    units: u.Unit | None


@dataclass(frozen=True)
class AstropySchema:
    # TODO: it would be nice to have units parsed from the response!
    NAME = DataColumn("Name", str, None)
    FREQUENCY = DataColumn("Frequency", np.float64, u.Hz)
    NUFNU = DataColumn("Nufnu", np.float64, u.erg / (u.cm**2 * u.s))
    FREQUENCY_ERROR = DataColumn("FrequencyError", np.float64, u.Hz)
    NUFNU_ERROR = DataColumn("NufnuError", np.float64, u.erg / (u.cm**2 * u.s))
    ANGULAR_DISTANCE = DataColumn("AngularDistance", np.float64, u.arcsec)
    START_TIME = DataColumn("StartTime", np.float64, u.d)
    STOP_TIME = DataColumn("StopTime", np.float64, u.d)
    INFO = DataColumn("Info", str, None)
    CATALOG_NAME = CatalogColumn("CatalogName", str, None)
    CATALOG_BAND = CatalogColumn("CatalogBand", str, None)
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
            yield self.CATALOG_NAME
            yield self.CATALOG_BAND
            yield self.ERROR_RADIUS

    def metadata(self):
        """Iterate over metadata, defines table order."""
        yield self.METADATA_NH


TABLE_SCHEMA = AstropySchema()


class Meta(BaseModel):
    """Metadata about the response format.

    Attributes:
        InfoSeparator: Character used to separate multiple values in the Info field.
    """

    InfoSeparator: str


class GetDataResponse(BaseModel):
    """SED Builder API response to `getData` endpoint.

    To retrieve data you call `.to_astropy()`, or `.to_dict()` and other methods.

    Attributes:
        ResponseInfo: Status information about the API response.
        Properties: Additional science properties for the queried source.
        Datasets: List of catalog entries with measurements.
        Meta: Extra, not scientific, information.
    """

    ResponseInfo: ResponseInfo
    Properties: Properties
    Datasets: list[Dataset]
    Meta: Meta

    def __repr__(self) -> str:
        return f"Response(status={self.ResponseInfo.statusCode!r}, " f"Datasets: [#{len(self.Datasets)} entries])"

    def is_successful(self) -> bool:
        """Check if the API response indicates success.

        Returns:
            True if the response status code is 'OK'.
        """
        return self.ResponseInfo.statusCode == "OK"

    def to_dict(self) -> dict:
        """Converts data to a dictionary.

        Returns:
            A dictionary from the response JSON.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Converts data to JSON.

        Returns:
            A JSON string.
        """
        return json.dumps(self.model_dump())

    def to_pandas(self) -> Any:
        """Converts data to a pandas DataFrame.

        Requires pandas to be installed. Install with `pip install pandas`.

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
            Astropy Table with one row per measurements.
        """
        # the gist of it is to build two different tables and to stack them horizontally.
        # the first table is for data columns, the second for the catalog columns.
        columns_data = [*TABLE_SCHEMA.columns(kind="data")]
        columns_catalog = [*TABLE_SCHEMA.columns(kind="catalog")]

        # first we have to unpack the data
        rows_data, rows_catalog = [], []
        for dataset in self.Datasets:
            catalog_dump = {k: v for k, v in dataset.Catalog.model_dump().items() if k in columns_catalog}
            for source_data in dataset.SourceData:
                rows_data.append(source_data.model_dump())
                rows_catalog.append(catalog_dump)

        # TODO: this is an awful hack around astropy 6, which we need to support over 3.10.
        #  remove when we stop supporting astropy 6.
        #  N! i am unsure on whether we could have catalog info without data. the contrary should not be possible.
        #  N! this said, no data means no science: it seems safe to me to just check for `rows_data`
        if not rows_data:
            columns = columns_data + columns_catalog
            table = Table(
                np.zeros(len(columns)),
                names=[col.name for col in columns],
                dtype=[col.dtype for col in columns],
                units=[col.units for col in columns],
            )[:0]
        else:
            # first, the column table
            table_data = Table(
                rows_data,
                names=[col.name for col in columns_data],
                dtype=[col.dtype for col in columns_data],
                units=[col.units for col in columns_data],
            )

            # second, the catalog property table
            table_catalog = Table(
                rows_catalog,
                names=[col.name for col in columns_catalog],
                dtype=[col.dtype for col in columns_catalog],
                units=[col.units for col in columns_catalog],
            )

            # then, we stack
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
            Field(ge=0.0, le=1.0, description="Confidence level for upper limits, must be between 0 and 1."),
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
        """Convert data to Jetset format.

        The output includes both the data table with renamed columns and appropriate units,
        plus metadata needed for Jetset analysis.

        Args:
            z: Source redshift, must be between 0 and 1.
            ul_cl: Confidence level for upper limits, must be between 0 and 1,
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
        # fmt: off
        t = self.to_astropy()
        table = Table()
        table.add_column(t[TABLE_SCHEMA.FREQUENCY.name].astype(np.float64), name="x")
        table.add_column(t[TABLE_SCHEMA.FREQUENCY_ERROR.name].astype(np.float64), name="dx")
        table.add_column(t[TABLE_SCHEMA.NUFNU.name].astype(np.float64), name="y")
        table.add_column(t[TABLE_SCHEMA.NUFNU_ERROR.name].astype(np.float64), name="dy")
        table.add_column(np.nan_to_num(t[TABLE_SCHEMA.START_TIME.name].value, nan=0.0).astype(np.float64), name="T_start")
        table.add_column(np.nan_to_num(t[TABLE_SCHEMA.STOP_TIME.name].value, nan=0.0).astype(np.float64), name="T_stop")
        table.add_column(
            [*map(
                lambda x: "Upper Limit" in x,
                [[*map(
                    lambda x: x.strip(),
                    str(s).split(self.Meta.InfoSeparator)
                )] for s in t["Info"]]
            )], name="UL")
        table.add_column(t[TABLE_SCHEMA.CATALOG_NAME.name].astype(str), name="dataset")
        table.meta["z"] = z
        table.meta["UL_CL"] = ul_cl
        table.meta["restframe"] = restframe
        table.meta["data_scale"] = data_scale
        table.meta["obj_name"] = obj_name
        # fmt: on
        return table


class CatalogsResponse(BaseModel):
    """SED Builder API response to `catalogs` endpoint.

    Contains information about all available catalogs in the SED Builder system,
    including their names, identifiers, error radii, and spectral classifications.

    Attributes:
        ResponseInfo: Status information about the API response.
        Catalogs: List of catalog information entries.
    """

    ResponseInfo: ResponseInfo
    Catalogs: list[Catalog]

    def is_successful(self) -> bool:
        """Check if the API response indicates success.

        Returns:
            True if the response status code is 'OK'.
        """
        return self.ResponseInfo.statusCode == "OK"

    def to_list(self) -> list[dict]:
        """Converts catalog data to a list of dictionaries.

        Returns:
            A list of dictionaries, one per catalog, containing all catalog metadata.
        """
        return [c.model_dump() for c in self.Catalogs]
