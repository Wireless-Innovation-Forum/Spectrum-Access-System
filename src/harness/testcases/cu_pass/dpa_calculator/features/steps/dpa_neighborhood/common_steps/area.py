from dataclasses import dataclass

from behave import *

from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.utilities import Point
from testcases.cu_pass.dpa_calculator.features.environment.hooks import ContextSas
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import get_arbitrary_coordinates

use_step_matcher('parse')


@dataclass
class ContextArea(ContextSas):
    area: AreaCircle


@step("a circular area with a radius of {radius_in_kilometers:Integer} km")
def step_impl(context: ContextArea, radius_in_kilometers: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.area = AreaCircle(
        center_coordinates=get_arbitrary_coordinates(),
        radius_in_kilometers=radius_in_kilometers
    )


@step("center coordinates {coordinates:LatLng}")
def step_impl(context: ContextArea, coordinates: Point):
    context.area.center_coordinates = coordinates
