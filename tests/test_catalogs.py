"""Tests for catalogs functionality."""

from pathlib import Path

import pytest

from sedbuilder import catalogs_from_json


class TestCatalogsConversions:
    """Test the catalog conversion."""

    def test_to_list_conversion(self):
        """Test to_list() method returns proper structure."""
        fixture = Path("tests/data/catalogs.json")
        if not fixture.exists():
            pytest.skip("Test data not available")

        response = catalogs_from_json(fixture)
        catalog_list = response.to_list()

        # Should return a list
        assert isinstance(catalog_list, list)
        assert len(catalog_list) > 0

        # Each item should be a dict with required fields
        for cat_dict in catalog_list:
            assert isinstance(cat_dict, dict)
            assert "CatalogName" in cat_dict
            assert "ErrorRadius" in cat_dict
            assert "CatalogId" in cat_dict
