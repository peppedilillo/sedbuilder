"""Tests for the `get_data` interface."""

import json
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from astropy.table import Table
from pydantic import ValidationError
import pytest

from sedbuilder import get_data_from_json
from sedbuilder.requests import get_data
from sedbuilder.schemas import TABLE_SCHEMA


@pytest.fixture
def mock_response():
    """Minimal valid API response for testing."""
    return {
        "ResponseInfo": {
            "statusCode": "OK",
            "message": None,
        },
        "Properties": {
            "Nh": 1e20,
            "Units": {
                "Frequency": "Hz",
                "FrequencyError": "Hz",
                "Nufnu": "erg cm**(-2) s**(-1)",
                "NufnuError": "erg cm**(-2) s**(-1)",
                "AngularDistance": "arcsec",
                "StartTime": "mjd",
                "StopTime": "mjd",
                "ErrorRadius": "arcsec",
                "Nh": "cm**-2",
            },
        },
        "Datasets": [],
        "Meta": {"InfoSeparator": ";"},
    }


class TestGetDataValidation:
    """Test coordinate validation for get_data function."""

    def test_valid_coordinates(self, mock_response):
        """Test that valid coordinates are accepted."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: mock_response)

            # Crab
            get_data(ra=83.6329, dec=22.0144)
            # Galactic center
            get_data(ra=266.4, dec=-29.0)

    def test_ra_boundaries(self, mock_response):
        """Test RA boundary values."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: mock_response)

            # Valid: minimum RA
            get_data(ra=0.0, dec=0.0)
            # Valid: just below upper bound
            get_data(ra=359.999, dec=0.0)
            # Invalid: at upper bound (exclusive)
            with pytest.raises(ValidationError):
                get_data(ra=360.0, dec=0.0)
            # Invalid: above upper bound
            with pytest.raises(ValidationError):
                get_data(ra=361.0, dec=0.0)
            # Invalid: negative RA
            with pytest.raises(ValidationError):
                get_data(ra=-1.0, dec=0.0)

    def test_dec_boundaries(self, mock_response):
        """Test Dec boundary values."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: mock_response)

            # Valid: South pole
            get_data(ra=0.0, dec=-90.0)
            # Valid: North pole
            get_data(ra=0.0, dec=90.0)
            # Invalid: below lower bound
            with pytest.raises(ValidationError):
                get_data(ra=0.0, dec=-90.001)
            # Invalid: above upper bound
            with pytest.raises(ValidationError):
                get_data(ra=0.0, dec=90.001)

    def test_invalid_types(self):
        """Test that invalid types are rejected."""
        with pytest.raises(ValidationError):
            get_data(ra="invalid", dec=0.0)

        with pytest.raises(ValidationError):
            get_data(ra=0.0, dec="invalid")

        with pytest.raises(ValidationError):
            get_data(ra=None, dec=0.0)

    def test_special_float_values(self):
        """Test special float values (NaN, Inf)."""
        with pytest.raises(ValidationError):
            get_data(ra=float("nan"), dec=0.0)

        with pytest.raises(ValidationError):
            get_data(ra=float("inf"), dec=0.0)

        with pytest.raises(ValidationError):
            get_data(ra=0.0, dec=float("-inf"))


class TestGetDataHTTP:
    """Test HTTP behavior of get_data function."""

    def test_correct_url_construction(self, mock_response):
        """Test that the correct URL is constructed."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: mock_response)

            get_data(ra=194.04625, dec=-5.789167)

            called_url = mock_get.call_args[0][0]
            assert "194.04625" in called_url
            assert "-5.789167" in called_url
            assert "getData" in called_url


class TestResponseConversions:
    """Test conversion methods on all fixtures."""

    @pytest.fixture
    def fixtures(self):
        data_dir = Path("tests/data")
        assert data_dir.exists()

        fixtures = [f for f in data_dir.glob("*.json") if f.name != "catalogs.json"]
        assert fixtures
        return fixtures

    def test_to_dict(self, fixtures):
        for fixture in fixtures:
            response = get_data_from_json(fixture)
            result = response.to_dict()
            assert isinstance(result, dict)
            assert "ResponseInfo" in result
            assert "Properties" in result
            assert "Datasets" in result

    def test_to_json(self, fixtures):
        for fixture in fixtures:
            response = get_data_from_json(fixture)
            result = response.to_json()
            assert isinstance(result, str)
            parsed = json.loads(result)
            assert isinstance(parsed, dict)

    def test_to_astropy(self, fixtures):
        for fixture in fixtures:
            response = get_data_from_json(fixture)
            table = response.to_astropy()
            assert isinstance(table, Table)

            for col in TABLE_SCHEMA.columns(kind="all"):
                assert col.name in table.colnames, f"Missing column: {col.name}"
                if col.dtype == str:
                    assert table[col.name].dtype.kind == "U", f"Wrong dtype for {col.name}"
                else:
                    assert table[col.name].dtype == col.dtype, f"Wrong dtype for {col.name}"
                if col.units is not None:
                    assert table[col.name].unit == col.units, f"Wrong unit for {col.name}"
                else:
                    assert table[col.name].unit is None, f"Expected no unit for {col.name}"

            for meta in TABLE_SCHEMA.metadata():
                assert meta.name in table.meta, f"Missing metadata: {meta.name}"

    def test_to_jetset(self, fixtures):
        for fixture in fixtures:
            response = get_data_from_json(fixture)
            table = response.to_jetset(z=0.1)
            assert isinstance(table, Table)
            assert "x" in table.colnames
            assert "y" in table.colnames
            assert "UL" in table.colnames
            assert "dataset" in table.colnames
            assert table.meta["z"] == 0.1
