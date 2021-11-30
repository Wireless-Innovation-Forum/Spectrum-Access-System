import random
from collections import defaultdict
from dataclasses import dataclass

import parse
from math import isclose
from typing import Callable, Iterable, List

from behave import *

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.utilities import Point, get_bearing_between_two_points, get_distance_between_two_points
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher('parse')


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
class ContextRandomApPositioning(ContextCbsdCreation, ContextArea):
    pass


@given("a seed of {seed:Integer}")
def step_impl(context: ContextRandomApPositioning, seed: int):
    """
    Args:
        context (behave.runner.Context):
    """
    random.seed(seed)


@then("all distributed points should be within the radius of the center point")
def step_impl(context: ContextRandomApPositioning):
    """
    Args:
        context (behave.runner.Context):
    """
    distribution_area = context.area
    assert all(_point_is_within_distance(point=point,
                                         center_point=distribution_area.center_coordinates,
                                         distance=distribution_area.radius_in_kilometers)
               for point in get_distributed_points(cbsds=context.cbsds))


def _point_is_within_distance(point: Point, center_point: Point, distance: float) -> bool:
    leeway = 0.001
    return get_distance_between_two_points(point1=center_point, point2=point) - leeway <= distance


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
    distance = aggregation_function(metric_function(context.area.center_coordinates, point) for point in get_distributed_points(
        cbsds=context.cbsds))
    assert isclose(distance, reference_distance, abs_tol=1), f'{distance} is not close to {reference_distance}'


@step("no points should have exactly the same latitude, longitude, or bearing")
def step_impl(context: ContextRandomApPositioning):
    """
    Args:
        context (behave.runner.Context):
    """
    properties = defaultdict(set)
    for point in get_distributed_points(cbsds=context.cbsds):
        properties['latitude'].add(point.latitude)
        properties['longitude'].add(point.longitude)
        properties['bearing'].add(get_bearing_between_two_points(point1=context.area.center_coordinates, point2=point))

    assert all(len(unique_property_values) == len(get_distributed_points(cbsds=context.cbsds)) for unique_property_values in properties.values())


def get_distributed_points(cbsds: List[Cbsd]) -> List[Point]:
    return [cbsd.location for cbsd in cbsds]
