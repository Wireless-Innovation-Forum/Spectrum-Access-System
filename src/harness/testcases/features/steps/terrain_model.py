import re
from dataclasses import dataclass

import parse
from behave import *
from behave import runner
from geopy import Point
from geopy.distance import geodesic

use_step_matcher("parse")


NUMBER_REGEX = r'-?[0-9]+.?[0-9]*'


@dataclass
class ContextTerrainModel(runner.Context):
    origin: Point
    new_location: Point


@parse.with_pattern(f'{NUMBER_REGEX}, ?{NUMBER_REGEX}')
def parse_lat_lng(text: str) -> Point:
    coordinates = re.compile(f'{NUMBER_REGEX}').findall(text)
    latitude, longitude = (float(coordinate) for coordinate in coordinates)
    return Point(
        latitude=latitude,
        longitude=longitude
    )


register_type(LatLng=parse_lat_lng)


@given("Mike starts at location {coordinates:LatLng}")
def step_impl(context: ContextTerrainModel, coordinates: Point):
    """
    :type context: behave.runner.Context
    """
    context.origin = Point(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude
    )


@when("Mike moves {kilometers:f} kilometers with bearing {bearing:f} degrees")
def step_impl(context: ContextTerrainModel, kilometers: float, bearing: float):
    """
    Args:
        context (behave.runner.Context):
    """
    context.new_location = geodesic(kilometers=kilometers).destination(point=context.origin, bearing=bearing)


@then("Mike is at location {coordinates:LatLng}")
def step_impl(context: ContextTerrainModel, coordinates: Point):
    """
    Args:
        context (behave.runner.Context):
    """
    assert context.new_location == coordinates, f'{context.new_location.format_decimal(altitude=False)} != {coordinates.format_decimal(altitude=False)}'
