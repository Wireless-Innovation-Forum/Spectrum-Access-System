from dataclasses import dataclass

from behave import *

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.utilities import Point

use_step_matcher('parse')


ARBITRARY_COORDINATES = {
    REGION_TYPE_RURAL: Point(latitude=37.779704, longitude=-122.417747),
    REGION_TYPE_SUBURBAN: Point(latitude=37.753571, longitude=-122.44803),
    REGION_TYPE_URBAN: Point(latitude=37.781941, longitude=-122.404195)
}


def get_arbitrary_coordinates(region_type: str = REGION_TYPE_RURAL) -> Point:
    return ARBITRARY_COORDINATES[region_type]


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
    context.antenna_coordinates = get_arbitrary_coordinates(region_type.upper())
