from dataclasses import dataclass

from behave import *
from behave import runner

from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from cu_pass.dpa_calculator.utilities import get_dpa_center, Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_dpa import parse_dpa

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
class ContextRegionType(runner.Context):
    antenna_coordinates: Point


REGION_TYPE_TO_DPA_NAME_MAP = {
    REGION_TYPE_DENSE_URBAN: 'BATH',
    REGION_TYPE_RURAL: 'MCKINNEY',
    REGION_TYPE_URBAN: 'MOORESTOWN'
}


def _get_fake_dpa(region_type: str) -> Dpa:
    center = get_arbitrary_coordinates(region_type=region_type.upper())
    return Dpa(protected_points=None, geometry=center.to_shapely())


@step("a {region_type} location")
def step_impl(context: ContextRegionType, region_type: str):
    """
    Args:
        context (behave.runner.Context):
        region_type (str):
    """
    region_type_capitalized = region_type.upper()
    dpa_name = REGION_TYPE_TO_DPA_NAME_MAP.get(region_type_capitalized)
    context.dpa = parse_dpa(dpa_name) if dpa_name else _get_fake_dpa(region_type=region_type_capitalized)
    context.antenna_coordinates = get_dpa_center(dpa=context.dpa)


def assign_arbitrary_dpa(context: ContextRegionType) -> None:
    arbitrary_region_type = REGION_TYPE_RURAL
    context.execute_steps(f'Given a {arbitrary_region_type} location')
