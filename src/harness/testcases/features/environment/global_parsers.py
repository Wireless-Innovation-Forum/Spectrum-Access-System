import re

import parse
from behave import *

from dpa_calculator.utils import Point


INTEGER_REGEX = r'-?[0-9]+(,[0-9]{3})*'
NUMBER_REGEX = rf'{INTEGER_REGEX}(\.[0-9]+)?'


@parse.with_pattern(INTEGER_REGEX)
def parse_integer(text: str) -> int:
    return int(text.replace(',', ''))


@parse.with_pattern(NUMBER_REGEX)
def parse_number(text: str) -> float:
    return float(text.replace(',', ''))


@parse.with_pattern(f'{NUMBER_REGEX}, ?{NUMBER_REGEX}')
def parse_lat_lng(text: str) -> Point:
    coordinates = re.compile(f'{NUMBER_REGEX}').findall(text)
    latitude, longitude = (float(coordinate) for coordinate in coordinates)
    return Point(
        latitude=latitude,
        longitude=longitude
    )


register_type(Integer=parse_integer)
register_type(LatLng=parse_lat_lng)
register_type(Number=parse_number)
