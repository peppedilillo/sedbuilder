from pathlib import Path

from pydantic import ValidationError
import pytest

from sedbuilder import catalogs_from_json
from sedbuilder import CatalogsResponse

CATALOGS_FIXTURE = Path("tests/fixtures/catalogs/catalogs.json")
CATALOGS_NONEXISTENT = Path("tests/fixtures/catalogs/nonexistent.json")


class TestCatalogsFromJson:
    """Test the catalogs_from_json utility function."""

    def test_load_valid_json(self):
        fixture = CATALOGS_FIXTURE
        assert fixture.exists()

        response = catalogs_from_json(fixture)
        assert response is not None
        assert isinstance(response, CatalogsResponse)
        assert hasattr(response, "response_info")
        assert hasattr(response, "catalogs")

    def test_response_structure(self):
        """Test that response has expected structure."""
        fixture = CATALOGS_FIXTURE
        assert fixture.exists()

        response = catalogs_from_json(fixture)

        # ResponseInfo should indicate success
        assert response.response_info.status_code == "OK"

        # Catalogs should be a non-empty list
        assert isinstance(response.catalogs, list)
        assert len(response.catalogs) > 0

        # Each catalog should have minimum required fields
        for catalog in response.catalogs:
            assert hasattr(catalog, "name")
            assert hasattr(catalog, "error_radius")
            assert hasattr(catalog, "id")
            # SubGroupName is optional
            assert hasattr(catalog, "band")

    def test_nonexistent_file(self):
        """Test that nonexistent file raises ValidationError."""
        with pytest.raises(ValidationError):
            catalogs_from_json(CATALOGS_NONEXISTENT)

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
