"""Tests for response parsing from fixtures."""

from pathlib import Path

import pytest

from sedbuilder import get_data_from_json


class TestFixtureParsing:
    """Test that all fixtures in tests/data parse correctly."""

    def test_all_fixtures_parse(self):
        data_dir = Path("tests/data")
        if not data_dir.exists():
            pytest.skip("Test data directory not found")

        fixtures = list(data_dir.glob("*.json"))
        if not fixtures:
            pytest.skip("No test fixtures found")

        fixtures = [f for f in fixtures if f.name != "README.json"]
        assert len(fixtures) > 0, "Expected at least one test fixture"

        for fixture in fixtures:
            response = get_data_from_json(fixture)
            assert response is not None, f"Failed to parse {fixture.name}"
