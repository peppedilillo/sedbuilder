"""Pydantic models for validating SSDC SED Builder API responses.

This module defines the schema for the JSON responses returned by the
SED Builder API, providing validation and type safety.
"""

from dataclasses import dataclass
import json
from typing import Annotated, Any, Literal, NamedTuple, Optional

from astropy.table import Column
from astropy.table import hstack
from astropy.table import Table
import astropy.units as u
import numpy as np
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import Field
from pydantic import validate_call


class ResponseInfo(BaseModel):
    """Response status information.

    Attributes:
        status_code: Status code of the response (e.g., 'OK', 'ERROR').
        message: Optional messages with additional information.
        api_version: API version code.
    """

    status_code: str = Field(alias="statusCode")
    message: Optional[list[str]] = None
    api_version: Optional[str] = Field(default=None, alias="APIVersion")


class Properties(BaseModel):
    """Additional properties for the queried source.

    Attributes:
        nh: Hydrogen column density in cm^-2 along the line of sight.
        units: Units of measure for data and properties..
    """

    nh: Optional[float] = Field(default=None, alias="Nh")
    units: Optional[dict[str, str]] = Field(default=None, alias="Units")


class Reference(BaseModel):
    """Literature reference metadata.

    Attributes:
        id: Reference ID.
        title: Reference title.
        authors: Reference author.
        url: Reference URL.
    """

    id: Optional[int] = Field(default=None, alias="Id")
    title: Optional[str] = Field(default=None, alias="Title")
    authors: Optional[str] = Field(default=None, alias="Authors")
    url: Optional[str] = Field(default=None, alias="URL")


class Source(BaseModel):
    """Catalog metadata.

    Attributes:
        kind: Source type (either "catalog" or "paper").
        name: Name of the astronomical catalog.
        id: Unique identifier for the catalog.
        error_radius: Search radius in arcsec used for source matching.
        band: Spectral band classification (e.g., 'Radio', 'Infrared', 'Optical').
        references: A list of literature reference metadata associated to this source.
    """

    kind: Literal["Catalog", "Paper"] = Field(alias="Kind")
    name: str = Field(alias="Name")
    id: int = Field(alias="Id")
    error_radius: Annotated[float, Field(ge=0.0)] = Field(alias="ErrorRadius")
    band: Optional[str] = Field(default=None, alias="Band")
    references: Optional[list[Reference]] = Field(default=None, alias="References")

    def __repr__(self) -> str:
        return (
            f"Source(Name={self.name!r}, "
            f"Kind={self.kind}, "
            f"Id={self.id}, "
            f"error_radius={self.error_radius}, "
            f"Band={self.band!r})"
        )


class Data(BaseModel):
    """Spectral energy distribution data point.

    Represents a single row from a data source.
    """

    frequency: Annotated[float, Field(gt=0.0)] = Field(alias="Frequency")
    nufnu: float = Field(alias="Nufnu")
    frequency_error: Annotated[float, Field(ge=0.0)] = Field(alias="FrequencyError")
    nufnu_error: float = Field(alias="NufnuError")
    name: Optional[str] = Field(default=None, alias="Name")
    angular_distance: Annotated[Optional[float], Field(default=None, ge=0.0)] = Field(
        default=None, alias="AngularDistance"
    )
    start_time: Annotated[Optional[float], Field(default=None, ge=0.0)] = Field(default=None, alias="StartTime")
    stop_time: Annotated[Optional[float], Field(default=None, ge=0.0)] = Field(default=None, alias="StopTime")
    info: Optional[str] = Field(default="", alias="Info")


class Dataset(BaseModel):
    """A catalog entry with its associated source data.

    Attributes:
        source: Metadata about the catalog.
        data: List of measurements from this catalog.
    """

    source: Source = Field(alias="Source")
    data: list[Data] = Field(alias="Data")

    def __repr__(self) -> str:
        return f"Dataset({self.source!r}, Data: [#{len(self.data)} entries])"


class DataColumn(NamedTuple):
    """Schema descriptor for a column sourced from a `Data` measurement.

    Attributes:
        name: Column name in the output astropy Table (matches the `Data` field name).
        dtype: NumPy or Python dtype for the column.
        units: Astropy unit, or ``None`` for dimensionless columns.
    """

    name: str  # field name in SourceData
    dtype: type
    units: u.Unit | None


class SourceColumn(NamedTuple):
    """Schema descriptor for a column sourced from a `Source` catalog entry.

    Attributes:
        name: Column name in the output astropy Table. More descriptive than the
            raw model field name to avoid ambiguity when tables are stacked.
        field: Corresponding field name in the `Source` model.
        dtype: NumPy or Python dtype for the column.
        units: Astropy unit, or ``None`` for dimensionless columns.
    """

    # the field name could be too generic to be used as column name
    name: str  # column name in the astropy table, essentially a more descriptive alias
    field: str  # field name in Source model
    dtype: type
    units: u.Unit | None


class PropertyMetadata(NamedTuple):
    """Schema descriptor for a scalar metadata entry sourced from `Properties`.

    Attributes:
        name: Field name in the `Properties` model; also used as the key in
            ``Table.meta``.
        units: Astropy unit, or ``None`` for dimensionless values.
    """

    name: str  # field name in Properties
    units: u.Unit | None


@dataclass(frozen=True)
class AstropySchema:
    """Frozen schema definition for the output astropy Table produced by `GetDataResponse.to_astropy`.

    Each class attribute is a `DataColumn`, `SourceColumn`, or `PropertyMetadata`
    descriptor. The `columns` and `metadata` methods yield them in the canonical
    output order.
    """

    # TODO: it would be nice to have units parsed from the response!
    NAME = DataColumn("name", str, None)
    FREQUENCY = DataColumn("frequency", np.float64, u.Hz)
    NUFNU = DataColumn("nufnu", np.float64, u.erg / (u.cm**2 * u.s))
    FREQUENCY_ERROR = DataColumn("frequency_error", np.float64, u.Hz)
    NUFNU_ERROR = DataColumn("nufnu_error", np.float64, u.erg / (u.cm**2 * u.s))
    ANGULAR_DISTANCE = DataColumn("angular_distance", np.float64, u.arcsec)
    START_TIME = DataColumn("start_time", np.float64, u.d)
    STOP_TIME = DataColumn("stop_time", np.float64, u.d)
    INFO = DataColumn("info", str, None)
    SOURCE_NAME = SourceColumn("source_name", "name", str, None)
    SOURCE_BAND = SourceColumn("source_band", "band", str, None)
    ERROR_RADIUS = SourceColumn("error_radius", "error_radius", np.float64, u.arcsec)
    METADATA_NH = PropertyMetadata("nh", u.cm**-2)

    def columns(self, kind: Literal["data", "source", "all"] = "all"):
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
        if kind == "all" or kind == "source":
            yield self.SOURCE_NAME
            yield self.SOURCE_BAND
            yield self.ERROR_RADIUS

    def metadata(self):
        """Iterate over metadata, defines table order."""
        yield self.METADATA_NH


TABLE_SCHEMA = AstropySchema()


class Meta(BaseModel):
    """Metadata about the response format and other non-science info.

    Attributes:
        info_separator: Character used to separate multiple values in the Info field.
    """

    info_separator: str = Field(alias="InfoSeparator")


class GetDataResponse(BaseModel):
    """SED Builder API response to `getData` endpoint.

    To retrieve data you call `.to_astropy()`, or `.to_dict()` and other methods.

    Attributes:
        response_info: Status information about the API response.
        properties: Additional science properties for the queried source.
        datasets: List of catalog entries with measurements.
        meta: Metadata about the response format and other non-science info.
    """

    response_info: ResponseInfo = Field(alias="ResponseInfo")
    properties: Properties = Field(alias="Properties")
    datasets: list[Dataset] = Field(alias="Datasets")
    meta: Meta = Field(alias="Meta")

    def __repr__(self) -> str:
        return f"Response(status={self.response_info.status_code!r}, " f"datasets: [#{len(self.datasets)} entries])"

    def is_successful(self) -> bool:
        """Check if the API response indicates success.

        Returns:
            True if the response status code is 'OK'.
        """
        return self.response_info.status_code == "OK"

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
        except ImportError:
            raise ImportError("pandas is required for this method. Install it with: pip install pandas")

    def to_astropy(self) -> Table:
        """Convert data to an astropy Table.

        Returns:
            Astropy Table with one row per measurements.
        """
        # the gist of it is to build two different tables and to stack them horizontally.
        # the first table is for data columns, the second for the catalog columns.
        columns_data = [*TABLE_SCHEMA.columns(kind="data")]
        columns_source = [*TABLE_SCHEMA.columns(kind="source")]

        # first we have to unpack the data
        rows_data, rows_source = [], []
        for dataset in self.datasets:
            _dsmp = dataset.source.model_dump()
            source_dump = {col.name: _dsmp[col.field] for col in columns_source if col.field in _dsmp}
            for source_data in dataset.data:
                rows_data.append(source_data.model_dump())
                rows_source.append(source_dump)

        # first, the column table
        table_data = Table(
            rows_data,
            names=[col.name for col in columns_data],
            dtype=[col.dtype for col in columns_data],
            units=[col.units for col in columns_data],
        )

        # second, the catalog property table
        table_source = Table(
            rows_source,
            names=[col.name for col in columns_source],
            dtype=[col.dtype for col in columns_source],
            units=[col.units for col in columns_source],
        )

        # then, we stack
        table = hstack((table_data, table_source))

        # and add metadata
        for m in TABLE_SCHEMA.metadata():
            table.meta[m.name] = getattr(self.properties, m.name)
            if m.units:
                table.meta[m.name] *= m.units
        return table

    @validate_call
    def to_jetset(
        self,
        z: Annotated[float, Field(ge=0.0, le=1.0)],
        ul_cl: Annotated[float, Field(ge=0.0, le=1.0)] = 0.95,
        restframe: Literal["obs", "src"] = "obs",
        data_scale: Literal["lin-lin", "log-log"] = "lin-lin",
        obj_name: str = "new-src",
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

        def info2ul(infos: Column) -> list[bool]:
            """Parses info column and checks where it contains 'Upper Limit' tag.'"""
            return ["Upper Limit" in [i.strip() for i in str(info).split(self.meta.info_separator)] for info in infos]

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
        table.add_column(info2ul(t[TABLE_SCHEMA.INFO.name]), name="UL")
        table.add_column(t[TABLE_SCHEMA.SOURCE_NAME.name].astype(str), name="dataset")
        table.meta["z"] = z
        table.meta["UL_CL"] = ul_cl
        table.meta["restframe"] = restframe
        table.meta["data_scale"] = data_scale
        table.meta["obj_name"] = obj_name
        # fmt: on
        return table

    def sources(self) -> list[dict]:
        """Returns a list of references to the catalog and papers from which the data is collected.

        Returns:
            Datasets source metadata.
        """
        return [d.source.model_dump() for d in self.datasets]


class CatalogsResponse(BaseModel):
    """SED Builder API response to `catalogs` endpoint.

    Contains information about all available catalogs in the SED Builder system,
    including their names, identifiers, error radii, and spectral classifications.

    Attributes:
        response_info: Status information about the API response.
        catalogs: List of catalog information entries.
    """

    response_info: ResponseInfo = Field(alias="ResponseInfo")
    catalogs: list[Source] = Field(alias="Catalogs")

    def is_successful(self) -> bool:
        """Check if the API response indicates success.

        Returns:
            True if the response status code is 'OK'.
        """
        return self.response_info.status_code == "OK"

    def to_list(self) -> list[dict]:
        """Converts catalog data to a list of dictionaries.

        Returns:
            A list of dictionaries, one per catalog, containing all catalog metadata.
        """
        return [c.model_dump() for c in self.catalogs]


class NameResolverItem(BaseModel):
    """A single result returned by the SSDC name resolver endpoint.

    Attributes:
        db: The resolver database that produced this result.
        ra: Right ascension in degrees.
        dec: Declination in degrees.
        id: Internal identifier assigned by the resolver database.
        name: Display name of the resolved source.
    """

    model_config = ConfigDict(populate_by_name=True)

    db: Literal["SSDC", "NED", "SIMBAD"] = Field(alias="valueDB")
    ra: Annotated[float, BeforeValidator(float)] = Field(alias="valueRA")
    dec: Annotated[float, BeforeValidator(float)] = Field(alias="valueDEC")
    id: Optional[str] = None
    name: str = Field(alias="text")


class NameResolverResponse(BaseModel):
    """Response from the SSDC name resolver endpoint.

    Attributes:
        results: List of candidate matches, potentially from multiple databases.
    """

    results: list[NameResolverItem]
