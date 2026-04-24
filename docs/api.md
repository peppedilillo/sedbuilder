# API Reference

This API reference describes the Python interface to the ASI-SSDC SED Builder service. 
The package provides functions to build spectral energy distributions (SEDs) for astronomical sources by querying data from multi-frequency catalogs and converting them into various output formats.

!!! note
    At present, only internally hosted catalogs are supported. More will come.

## Functions

::: sedbuilder.requests.get_data
::: sedbuilder.utils.get_data_from_json
::: sedbuilder.requests.catalogs
::: sedbuilder.utils.catalogs_from_json
::: sedbuilder.requests.resolve_name

## Classes

::: sedbuilder.schemas.GetDataResponse
::: sedbuilder.schemas.CatalogsResponse