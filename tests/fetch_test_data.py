"""Fetch SED data for test sources and save as JSON files.

This script queries the SED Builder API for a predefined list of astronomical
sources and saves the responses as JSON files. Run this script whenever the
upstream API changes to update test fixtures with the latest data format.

Usage:
    python tests/fetch_test_data.py
"""

import json
from pathlib import Path
from time import sleep

import httpx

from sedbuilder._endpoints import APIPaths

TEST_SOURCES = [
    (343.49061, +16.14821, "3C 454.3"),  # Bright blazar
    (166.1138086814600, +38.2088329155200, "Mrk 421"),  # TeV blazar
    (329.71693, -30.22558, "PKS 2155-304"),  # Southern blazar
    (083.6324, +22.0174, "Crab Nebula"),  # SNR/pulsar
    (128.83606354, -45.17643181, "Vela Pulsar"),  # Gamma-ray pulsar
    (201.365063, -43.019112, "Centaurus A"),  # Nearby AGN
    (299.590315, +35.20160, "Cygnus X-1"),  # Black hole binary
    (161.2500, +58.0000, "Lockman Hole"),  # Empty field
    (0.0, 90.0, "North Pole"),  # Edge case
    (266.41500889, -29.00611111, "Galactic Center"),  # Sgr A*
]


def format_filename(ra: float, dec: float, source_name: str) -> str:
    """Format coordinates and source name into filename.

    Args:
        ra: Right ascension in degrees.
        dec: Declination in degrees.
        source_name: Name of the astronomical source.

    Returns:
        Filename in format: {source_name}_{ra}_{dec}.json with special characters replaced.

    Example:
        >>> format_filename(194.04625, -5.789167, "M87")
        'm87_194d04625_m5d789167.json'
    """
    name_str = "".join(c for c in source_name.lower() if c.isalnum())
    ra_str = f"{ra:.5f}".replace(".", "d").replace("+", "p")
    dec_str = f"{dec:.5f}".replace(".", "d").replace("+", "p").replace("-", "m")
    return f"{ra_str}_{dec_str}_{name_str}.json"


def fetch_and_save_test_data(output_dir: Path = Path("data"), timeout: int = 10) -> None:
    """Fetch test data and catalogs from API and save as JSON files.

    Args:
        output_dir: Directory to save JSON files (default: tests/data).
        timeout: Timeout in seconds (default: 10).
    """
    print(f"Output directory: {output_dir.absolute()}\n")

    print(f"Fetching test data for {len(TEST_SOURCES)} sources...")
    for ra, dec, description in TEST_SOURCES:
        filename = format_filename(ra, dec, description)
        filepath_source = output_dir / filename
        print(f"Fetching {description} (RA={ra}, Dec={dec})...", end=" ")
        try:
            response = httpx.get(APIPaths.GET_DATA(ra=ra, dec=dec), timeout=timeout)
            filepath_source.write_text(json.dumps(response.json(), indent=2))
            print(f" Saved to {filename}")
        except Exception as e:
            print(f" Failed: {e}")
        sleep(1.0)

    print(f"Fetching catalogs data..")
    filepath_catalog = output_dir / "catalogs.json"
    try:
        response = httpx.get(APIPaths.CATALOGS(), timeout=timeout)
        filepath_catalog.write_text(json.dumps(response.json(), indent=2))
        print(f" Saved to {filepath_catalog}")
    except Exception as e:
        print(f" Failed: {e}")

    print(f"\nComplete. Test data saved to {output_dir.absolute()}")


if __name__ == "__main__":
    fetch_and_save_test_data()
