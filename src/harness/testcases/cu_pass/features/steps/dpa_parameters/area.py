from dataclasses import dataclass

from behave import *
from behave import runner

from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point


@dataclass
class ContextArea(runner.Context):
    area: AreaCircle


@step("a circular area with a radius of {radius_in_kilometers:Integer} km and center coordinates {coordinates:LatLng}")
def step_impl(context: ContextArea, radius_in_kilometers: int, coordinates: Point):
    """
    Args:
        context (behave.runner.Context):
    """
    context.area = AreaCircle(
        center_coordinates=coordinates,
        radius_in_kilometers=radius_in_kilometers
    )
