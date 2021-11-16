import re
from dataclasses import dataclass
from typing import List

from behave import *
from behave import runner

from dpa_calculator.utils import Point, move_distance
from testcases.cu_pass.features.environment.hooks import ContextSas


@dataclass
class ContextMoving(ContextSas):
    origin: Point
    new_location: Point


@dataclass
class ContextProfile(ContextSas):
    terrain_model: List[float]


@given("Mike starts at location {coordinates:LatLng}")
def step_impl(context: ContextMoving, coordinates: Point):
    """
    :type context: behave.runner.Context
    """
    context.origin = Point(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude
    )


@when("Mike moves {kilometers:f} kilometers with bearing {bearing:f} degrees")
def step_impl(context: ContextMoving, kilometers: float, bearing: float):
    """
    Args:
        context (behave.runner.Context):
    """
    context.new_location = move_distance(bearing=bearing, origin=context.origin, kilometers=kilometers)


@then("Mike is at location {coordinates:LatLng}")
def step_impl(context: ContextMoving, coordinates: Point):
    """
    Args:
        context (behave.runner.Context):
    """
    assert context.new_location == coordinates, f'{context.new_location} != {coordinates}'


# @given("Coordinates {point1:LatLng} and {point2:LatLng}")
# def step_impl(context: ContextProfile, ):
#     """
#     Args:
#         context (behave.runner.Context):
#     """
#     expected_terrain_model = get_expected_terrain_model()
#     raise NotImplementedError(u'STEP: Given Coordinates 40.81734, -121.46933 and 40.096901173373254, -121.46933')
