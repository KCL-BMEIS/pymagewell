# content of conftest.py
from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--hardware_mode",
        action="store",
        default="True",
        help="Set to true to run tests on hardware (requires video signal)",
    )


@pytest.fixture
def hardware_mode(request: Any) -> None:
    try:
        if request.config.getoption("--hardware") == "True":
            print("Hardware test mode enabled")
            request.cls.hardware_mode_is_set = True
        elif request.config.getoption("--hardware") == "False":
            print("Hardware test mode disabled")
            request.cls.hardware_mode_is_set = False
        else:
            raise ValueError("hardware_mode option must be set to either 'True' or 'False'")
    except ValueError:
        print("Hardware test mode disabled")
        request.cls.hardware_mode_is_set = False
