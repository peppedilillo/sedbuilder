"""Tests for response conversion methods."""

import json
from pathlib import Path

from astropy.table import Table
import pytest

from sedbuilder import get_data_from_json
from sedbuilder.schemas import TABLE_SCHEMA


class TestResponseConversions:
    """Test conversion methods on all fixtures."""

    @pytest.fixture
    def fixtures(self):
        data_dir = Path("tests/data")
        if not data_dir.exists():
            pytest.skip("Test data directory not found")
        fixtures = [f for f in data_dir.glob("*.json") if f.name != "README.json"]
        if not fixtures:
            pytest.skip("No test fixtures found")
        return fixtures

    def test_to_dict(self, fixtures):
        for fixture in fixtures:
            response = get_data_from_json(fixture)
            result = response.to_dict()
            assert isinstance(result, dict)
            assert "ResponseInfo" in result
            assert "Properties" in result
            assert "Catalogs" in result

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
