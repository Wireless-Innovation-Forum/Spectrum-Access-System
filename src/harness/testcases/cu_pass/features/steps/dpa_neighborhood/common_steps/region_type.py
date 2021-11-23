from dataclasses import dataclass

from behave import *

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.utils import Point


ARBITRARY_COORDINATES = {
    REGION_TYPE_RURAL: Point(latitude=37.779704, longitude=-122.417747),
    REGION_TYPE_SUBURBAN: Point(latitude=37.753571, longitude=-122.44803),
    REGION_TYPE_URBAN: Point(latitude=37.781941, longitude=-122.404195)
}


@dataclass
class ContextRegionType:
    antenna_coordinates: Point


@step("a {region_type} location")
def step_impl(context: ContextRegionType, region_type: str):
    """
    Args:
        context (behave.runner.Context):
        region_type (str):
    """
    context.antenna_coordinates = ARBITRARY_COORDINATES[region_type.upper()]
