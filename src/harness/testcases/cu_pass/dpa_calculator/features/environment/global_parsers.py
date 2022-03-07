import re
from typing import List

import parse
from behave import *

from cu_pass.dpa_calculator.helpers.parsers import INTEGER_REGEX, NUMBER_REGEX, parse_number
from cu_pass.dpa_calculator.utilities import Point


def get_list_regex(item_regex: str) -> str:
    return rf'\[({item_regex},? ?)*\]'


NUMBER_LIST_REGEX = get_list_regex(item_regex=NUMBER_REGEX)
COORDINATES_REGEX = rf'{NUMBER_REGEX}, ?{NUMBER_REGEX}'


@parse.with_pattern('.*')
def parse_any(text: str) -> str:
    return text


@parse.with_pattern('.*')
def parse_string(text: str) -> str:
    return text


@parse.with_pattern(INTEGER_REGEX)
def parse_integer(text: str) -> int:
    integer_text = re.compile(INTEGER_REGEX).search(text)
    return int(integer_text[0].replace(',', ''))


@parse.with_pattern(get_list_regex(item_regex=INTEGER_REGEX))
def parse_integer_list(text: str) -> List[int]:
    numbers = re.compile(f'({INTEGER_REGEX})').findall(text)
    return [int(number[0]) for number in numbers]


@parse.with_pattern(NUMBER_LIST_REGEX)
def parse_number_list(text: str) -> List[float]:
    numbers = re.compile(f'({NUMBER_REGEX})').findall(text)
    return [float(number[0]) for number in numbers]


@parse.with_pattern(get_list_regex(item_regex=NUMBER_LIST_REGEX))
def parse_number_list_list(text: str) -> List[List[float]]:
    number_list_texts = re.compile(f'({NUMBER_LIST_REGEX})').findall(text)
    return [parse_number_list(text=number_list_text[0]) for number_list_text in number_list_texts]


@parse.with_pattern(COORDINATES_REGEX)
def parse_lat_lng(text: str) -> Point:
    coordinates = re.compile(f'({NUMBER_REGEX})').findall(text)
    latitude, longitude = (float(coordinate[0]) for coordinate in coordinates)
    return Point(
        latitude=latitude,
        longitude=longitude
    )


register_type(Any=parse_any)
register_type(Integer=parse_integer)
register_type(IntegerList=parse_integer_list)
register_type(LatLng=parse_lat_lng)
register_type(Number=parse_number)
register_type(NumberList=parse_number_list)
register_type(NumberListList=parse_number_list_list)
register_type(String=parse_string)
