"""Smoke tests: real HTTP requests to verify the live server is working.

Excluded from the default pytest run. To execute:
    pytest --smoke -m smoke
"""

import pytest

from sedbuilder import catalogs
from sedbuilder import get_data


@pytest.mark.smoke
class TestSmoke:
    def test_catalogs(self):
        response = catalogs()
        assert response.is_successful()
        assert len(response.to_list()) > 0

    def test_get_data_by_coords(self):
        response = get_data(ra=83.6324, dec=22.0174)  # Crab Nebula
        assert response.is_successful()

    def test_get_data_by_name(self):
        response = get_data(name="Crab Nebula")
        assert response.is_successful()

    def test_get_data_with_catalog_ids(self):
        response = get_data(ra=194.04625, dec=-5.789167, catalog_ids=(85, 5092))
        catalog_ids = [d.source.id for d in response.datasets]
        assert len(catalog_ids) == 2 and 85 in catalog_ids and 5092 in catalog_ids
