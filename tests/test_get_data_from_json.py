"""Tests for get_data_from_json."""

from pathlib import Path

from pydantic import ValidationError
import pytest

from sedbuilder import get_data_from_json


class TestGetDataFromJson:
    """Test the get_data_from_json utility function."""

    def test_load_valid_json(self):
        fixture = Path("tests/data/161d25000_58d00000_lockmanhole.json")
        if not fixture.exists():
            pytest.skip("Test data not available")

        response = get_data_from_json(fixture)
        assert response is not None
        assert hasattr(response, "ResponseInfo")
        assert hasattr(response, "Properties")
        assert hasattr(response, "Catalogs")

    def test_nonexistent_file(self):
        with pytest.raises(ValidationError):
            get_data_from_json("tests/data/nonexistent.json")

    def test_invalid_json(self, tmp_path):
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        with pytest.raises(ValidationError):
            get_data_from_json(invalid_file)

    def test_json_wrong_schema(self, tmp_path):
        wrong_schema = tmp_path / "wrong.json"
        wrong_schema.write_text('{"foo": "bar"}')

        with pytest.raises(ValidationError):
            get_data_from_json(wrong_schema)


class TestFixtureParsing:
    """Test that all fixtures in tests/data parse correctly."""

    def test_all_fixtures_parse(self):
        data_dir = Path("tests/data")
        if not data_dir.exists():
            pytest.skip("Test data directory not found")

        fixtures = [f for f in data_dir.glob("*.json") if f.name != "catalogs.json"]
        if not fixtures:
            pytest.skip("No test fixtures found")

        fixtures = [f for f in fixtures if f.name != "README.json"]
        assert len(fixtures) > 0, "Expected at least one test fixture"

        for fixture in fixtures:
            response = get_data_from_json(fixture)
            assert response is not None, f"Failed to parse {fixture.name}"
