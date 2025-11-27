from pathlib import Path

from pydantic import ValidationError
import pytest

from sedbuilder import catalogs_from_json
from sedbuilder import CatalogsResponse


class TestCatalogsFromJson:
    """Test the catalogs_from_json utility function."""

    def test_load_valid_json(self):
        fixture = Path("tests/data/catalogs.json")
        if not fixture.exists():
            pytest.skip("Test data not available")

        response = catalogs_from_json(fixture)
        assert response is not None
        assert isinstance(response, CatalogsResponse)
        assert hasattr(response, "ResponseInfo")
        assert hasattr(response, "Catalogs")

    def test_response_structure(self):
        """Test that response has expected structure."""
        fixture = Path("tests/data/catalogs.json")
        if not fixture.exists():
            pytest.skip("Test data not available")

        response = catalogs_from_json(fixture)

        # ResponseInfo should indicate success
        assert response.ResponseInfo.statusCode == "OK"

        # Catalogs should be a non-empty list
        assert isinstance(response.Catalogs, list)
        assert len(response.Catalogs) > 0

        # Each catalog should have minimum required fields
        for catalog in response.Catalogs:
            assert hasattr(catalog, "CatalogName")
            assert hasattr(catalog, "ErrorRadius")
            assert hasattr(catalog, "CatalogId")
            # SubGroupName is optional
            assert hasattr(catalog, "SubGroupName")

    def test_nonexistent_file(self):
        """Test that nonexistent file raises ValidationError."""
        with pytest.raises(ValidationError):
            catalogs_from_json("tests/data/nonexistent.json")

    def test_invalid_json(self, tmp_path):
        """Test that invalid JSON raises ValidationError."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        with pytest.raises(ValidationError):
            catalogs_from_json(invalid_file)

    def test_json_wrong_schema(self, tmp_path):
        """Test that JSON with wrong schema raises ValidationError."""
        wrong_schema = tmp_path / "wrong.json"
        wrong_schema.write_text('{"foo": "bar"}')

        with pytest.raises(ValidationError):
            catalogs_from_json(wrong_schema)
