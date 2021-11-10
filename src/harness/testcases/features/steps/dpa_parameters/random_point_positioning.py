import random
from collections import defaultdict
from dataclasses import dataclass

import parse
from math import isclose
from typing import Callable, Iterable, List

from behave import *
from behave import runner

from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point, get_bearing_between_two_points, get_distance_between_two_points
from reference_models.geo.vincenty import GeodesicPoint


BEARING_REGEX = 'bearing'
CLOSEST_REGEX = 'closest'
DISTANCE_REGEX = 'distance'
FURTHEST_REGEX = 'furthest'
HIGHEST_REGEX = 'highest'
LOWEST_REGEX = 'lowest'


@parse.with_pattern(f'({CLOSEST_REGEX}|{FURTHEST_REGEX}|{HIGHEST_REGEX}|{LOWEST_REGEX})')
def parse_min_max(text: str) -> Callable[[Iterable[float]], float]:
    return min if text in [CLOSEST_REGEX, LOWEST_REGEX] else max


@parse.with_pattern(f'({DISTANCE_REGEX}|{BEARING_REGEX})')
def parse_distance_or_bearing_word(text: str) -> Callable[[Point, Point], float]:
    return get_distance_between_two_points if text == DISTANCE_REGEX else get_bearing_between_two_points


register_type(MinMax=parse_min_max)
register_type(DistanceOrBearingFunction=parse_distance_or_bearing_word)


@dataclass
class ContextRandomApPositioning(runner.Context):
    number_of_points_to_distribute: int
    distribution_area: AreaCircle
    distributed_points: List[Point]


@given("{number_of_aps:Integer} geographic Points")
def step_impl(context: ContextRandomApPositioning, number_of_aps: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.number_of_points_to_distribute = number_of_aps


@step("a seed of {seed:Integer}")
def step_impl(context: ContextRandomApPositioning, seed: int):
    """
    Args:
        context (behave.runner.Context):
    """
    random.seed(seed)


@step("a circular area with a radius of {radius_in_kilometers:Integer} km and center coordinates {coordinates:LatLng}")
def step_impl(context: ContextRandomApPositioning, radius_in_kilometers: int, coordinates: Point):
    """
    Args:
        context (behave.runner.Context):
    """
    context.distribution_area = AreaCircle(
        center_coordinates=coordinates,
        radius_in_kilometers=radius_in_kilometers
    )


@when("the points are randomly distributed")
def step_impl(context: ContextRandomApPositioning):
    """
    Args:
        context (behave.runner.Context):
    """
    context.distributed_points = PointDistributor(distribution_area=context.distribution_area).distribute_points(number_of_points=context.number_of_points_to_distribute)


@then("all distributed points should be within the radius of the center point")
def step_impl(context: ContextRandomApPositioning):
    """
    Args:
        context (behave.runner.Context):
    """
    distribution_area = context.distribution_area
    assert all(_point_is_within_distance(point=point, center_point=distribution_area.center_coordinates, distance=distribution_area.radius_in_kilometers)
               for point in context.distributed_points)


def _point_is_within_distance(point: Point, center_point: Point, distance: float) -> bool:
    return get_distance_between_two_points(point1=center_point, point2=point) <= distance


@step("the {aggregation_function:MinMax} {metric_function:DistanceOrBearingFunction} should be close to {reference_distance:Integer} {_units}")
def step_impl(context: ContextRandomApPositioning,
              *args,
              metric_function: Callable[[Point, Point], float],
              aggregation_function:Callable[[Iterable[float]], float],
              reference_distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    distance = aggregation_function(metric_function(context.distribution_area.center_coordinates, point) for point in context.distributed_points)
    assert isclose(distance, reference_distance, abs_tol=1), f'{distance} is not close to {reference_distance}'


@step("no points should have exactly the same latitude, longitude, or bearing")
def step_impl(context: ContextRandomApPositioning):
    """
    Args:
        context (behave.runner.Context):
    """
    properties = defaultdict(set)
    for point in context.distributed_points:
        properties['latitude'].add(point.latitude)
        properties['longitude'].add(point.longitude)
        properties['bearing'].add(get_bearing_between_two_points(point1=context.distribution_area.center_coordinates, point2=point))

    assert all(len(unique_property_values) == len(context.distributed_points) for unique_property_values in properties.values())
