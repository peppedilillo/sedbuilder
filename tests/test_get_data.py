"""Tests for the `get_data` interface."""

from unittest.mock import Mock
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from sedbuilder.requests import get_data


@pytest.fixture
def mock_response():
    """Minimal valid API response for testing."""
    return {"ResponseInfo": {"statusCode": "OK", "message": None}, "Properties": {"Nh": 1e20}, "Catalogs": []}


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
