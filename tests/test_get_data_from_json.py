"""Tests for get_data_from_json."""

from pathlib import Path

from pydantic import ValidationError
import pytest

from sedbuilder import get_data_from_json

GET_DATA_DIR = Path("tests/fixtures/getData")
LOCKMANHOLE_FIXTURE = GET_DATA_DIR / "161d25000_58d00000_lockmanhole.json"


class TestGetDataFromJson:
    """Test the get_data_from_json utility function."""

    def test_load_valid_json(self):
        fixture = LOCKMANHOLE_FIXTURE
        assert fixture.exists()

        response = get_data_from_json(fixture)
        assert response is not None
        assert hasattr(response, "response_info")
        assert hasattr(response, "properties")
        assert hasattr(response, "datasets")

    def test_nonexistent_file(self):
        with pytest.raises(ValidationError):
            get_data_from_json("tests/nonexistent.json")

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
        data_dir = GET_DATA_DIR
        assert data_dir.exists()

        fixtures = [f for f in data_dir.glob("*.json") if f.name != "catalogs.json"]
        if not fixtures:
            pytest.skip("No test fixtures found")

        fixtures = [f for f in fixtures if f.name != "README.json"]
        assert len(fixtures) > 0, "Expected at least one test fixture"

        for fixture in fixtures:
            response = get_data_from_json(fixture)
            assert response is not None, f"Failed to parse {fixture.name}"
