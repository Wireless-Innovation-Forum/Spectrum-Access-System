from dataclasses import dataclass

from behave import *

from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers import parse_dpa

use_step_matcher('parse')


ARBITRARY_COORDINATES = {
    REGION_TYPE_DENSE_URBAN: Point(latitude=37.751113, longitude=-122.449722),
    REGION_TYPE_RURAL: Point(latitude=37.779704, longitude=-122.417747),
    REGION_TYPE_SUBURBAN: Point(latitude=37.753571, longitude=-122.44803),
    REGION_TYPE_URBAN: Point(latitude=37.781941, longitude=-122.404195)
}


def get_arbitrary_coordinates(region_type: str = REGION_TYPE_RURAL) -> Point:
    return ARBITRARY_COORDINATES[region_type]


@dataclass
class ContextRegionType:
    antenna_coordinates: Point


REGION_TYPE_TO_DPA_NAME_MAP = {
    REGION_TYPE_DENSE_URBAN: 'BATH',
    REGION_TYPE_RURAL: 'MCKINNEY',
    REGION_TYPE_URBAN: 'MOORESTOWN'
}


@step("a {region_type} location")
def step_impl(context: ContextRegionType, region_type: str):
    """
    Args:
        context (behave.runner.Context):
        region_type (str):
    """
    region_type_capitalized = region_type.upper()
    dpa_name = REGION_TYPE_TO_DPA_NAME_MAP.get(region_type_capitalized)
    dpa = dpa_name and parse_dpa(REGION_TYPE_TO_DPA_NAME_MAP[region_type_capitalized])
    context.dpa = dpa
    context.antenna_coordinates = Point.from_shapely(point_shapely=dpa.geometry.centroid) if dpa else get_arbitrary_coordinates(region_type_capitalized)
