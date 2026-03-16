"""Fetch SED data for test sources and save as JSON files.

This script queries the SED Builder API for a predefined list of astronomical
sources and saves the responses as JSON files. Run this script whenever the
upstream API changes to update test fixtures with the latest data format.

Usage:
    python tests/fetch_fixtures.py [--no-data] [--no-catalogs] [--no-names]
"""

import argparse
import itertools
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
    (266.41500889, -29.00611111, "Sgr A*"),  # Sgr A*
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


def fetch_and_save_test_data(
    output_dir: Path = Path("fixtures"),
    timeout: int = 30,
    fetch_data: bool = True,
    fetch_catalogs: bool = True,
    fetch_names: bool = True,
) -> None:
    """Fetch test data and catalogs from API and save as JSON files.

    Args:
        output_dir: Root directory for fixtures (default: fixtures).
        timeout: Timeout in seconds (default: 10).
        fetch_data: Whether to fetch source SED data (default: True).
        fetch_catalogs: Whether to fetch catalogs data (default: True).
        fetch_names: Whether to fetch name resolver data (default: True).
    """
    dir_get_data = output_dir / "getData"
    dir_catalogs = output_dir / "catalogs"
    dir_nameresolver = output_dir / "nameresolver"

    print(f"Output directory: {output_dir.absolute()}\n")

    if not fetch_data:
        print("Skipping source SED data.")
    else:
        dir_get_data.mkdir(parents=True, exist_ok=True)
        print(f"Fetching test data for {len(TEST_SOURCES)} sources...")
        for ra, dec, description in TEST_SOURCES:
            filename = format_filename(ra, dec, description)
            filepath_source = dir_get_data / filename
            print(f"Fetching {description} (RA={ra}, Dec={dec})...", end=" ")
            try:
                print(APIPaths.GET_DATA(ra=ra, dec=dec))
                response = httpx.get(APIPaths.GET_DATA(ra=ra, dec=dec), timeout=timeout)
                filepath_source.write_text(json.dumps(response.json(), indent=2))
                print(f" Saved to {filepath_source}")
            except Exception as e:
                print(f" Failed: {e}")
            sleep(1.0)

    if not fetch_catalogs:
        print("Skipping catalogs data.")
    else:
        dir_catalogs.mkdir(parents=True, exist_ok=True)
        print(f"Fetching catalogs data..")
        filepath_catalog = dir_catalogs / "catalogs.json"
        try:
            response = httpx.get(APIPaths.CATALOGS(), timeout=timeout)
            filepath_catalog.write_text(json.dumps(response.json(), indent=2))
            print(f" Saved to {filepath_catalog}")
        except Exception as e:
            print(f" Failed: {e}")

    if not fetch_names:
        print("Skipping name resolver data.")
    else:
        dir_nameresolver.mkdir(parents=True, exist_ok=True)
        _, _, first_source_name = TEST_SOURCES[0]
        name_slug = "".join(c for c in first_source_name.lower() if c.isalnum() or c == " ").replace(" ", "_")
        flag_combinations = list(itertools.product([True, False], repeat=3))
        print(f"Fetching name resolver data for '{first_source_name}' ({len(flag_combinations)} flag combinations)...")
        for ssdc, simbad, ned in flag_combinations:
            flags_str = f"ssdc{int(ssdc)}_simbad{int(simbad)}_ned{int(ned)}"
            filepath_nameresolver = dir_nameresolver / f"{name_slug}_{flags_str}.json"
            print(f"Resolving '{first_source_name}' (ssdc={ssdc}, simbad={simbad}, ned={ned})...", end=" ")
            try:
                url = APIPaths.NAME_RESOLVER(name=first_source_name, ssdc=ssdc, simbad=simbad, ned=ned)
                print(f"URL: {url}", end=" ")
                response = httpx.get(url, timeout=timeout)
                filepath_nameresolver.write_text(json.dumps(response.json(), indent=2))
                print(f"Saved to {filepath_nameresolver.name}")
            except Exception as e:
                print(f"Failed: {e}")
            sleep(1.0)

        print(f"Fetching name resolver data for remaining {len(TEST_SOURCES) - 1} sources (ssdc=T, simbad=T, ned=T)...")
        for _, _, source_name in TEST_SOURCES[1:]:
            name_slug = "".join(c for c in source_name.lower() if c.isalnum() or c == " ").replace(" ", "_")
            filepath_nameresolver = dir_nameresolver / f"{name_slug}_ssdc1_simbad1_ned1.json"
            print(f"Resolving '{source_name}'...", end=" ")
            try:
                url = APIPaths.NAME_RESOLVER(name=source_name, ssdc=True, simbad=True, ned=True)
                print(f"URL: {url}", end=" ")
                response = httpx.get(url, timeout=timeout)
                filepath_nameresolver.write_text(json.dumps(response.json(), indent=2))
                print(f"Saved to {filepath_nameresolver.name}")
            except Exception as e:
                print(f"Failed: {e}")
            sleep(1.0)

    print(f"\nComplete. Test data saved to {output_dir.absolute()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch SED Builder API test fixtures.")
    parser.add_argument("--no-data", action="store_true", help="Skip fetching source SED data.")
    parser.add_argument("--no-catalogs", action="store_true", help="Skip fetching catalogs data.")
    parser.add_argument("--no-names", action="store_true", help="Skip fetching name resolver data.")
    args = parser.parse_args()
    fetch_and_save_test_data(
        fetch_data=not args.no_data,
        fetch_catalogs=not args.no_catalogs,
        fetch_names=not args.no_names,
    )
