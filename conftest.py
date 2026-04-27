import pytest


def pytest_addoption(parser):
    parser.addoption("--smoke", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--smoke"):
        skip = pytest.mark.skip(reason="pass --smoke to run against the live server")
        for item in items:
            if "smoke" in item.keywords:
                item.add_marker(skip)
