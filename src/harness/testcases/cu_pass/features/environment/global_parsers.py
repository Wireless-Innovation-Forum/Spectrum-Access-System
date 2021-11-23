import re
from typing import List

import parse
from behave import *

from dpa_calculator.utils import Point


INTEGER_REGEX = r'-?[0-9]+(,[0-9]{3})*'
NUMBER_REGEX = rf'{INTEGER_REGEX}(\.[0-9]+)?'
COORDINATES_REGEX = rf'{NUMBER_REGEX}, ?{NUMBER_REGEX}'


@parse.with_pattern('.*')
def parse_string(text: str) -> str:
    return text


@parse.with_pattern(INTEGER_REGEX)
def parse_integer(text: str) -> int:
    return int(text.replace(',', ''))


@parse.with_pattern(NUMBER_REGEX)
def parse_number(text: str) -> float:
    return float(text.replace(',', ''))


@parse.with_pattern(f'\[({NUMBER_REGEX},? ?)+\]')
def parse_number_list(text: str) -> List[float]:
    numbers = re.compile(f'({NUMBER_REGEX})').findall(text)
    return [float(number[0]) for number in numbers]


@parse.with_pattern(COORDINATES_REGEX)
def parse_lat_lng(text: str) -> Point:
    coordinates = re.compile(f'({NUMBER_REGEX})').findall(text)
    latitude, longitude = (float(coordinate[0]) for coordinate in coordinates)
    return Point(
        latitude=latitude,
        longitude=longitude
    )


register_type(Integer=parse_integer)
register_type(LatLng=parse_lat_lng)
register_type(Number=parse_number)
register_type(NumberList=parse_number_list)
register_type(String=parse_string)
