import re
from dataclasses import dataclass
from typing import Optional

import parse
from behave import *

from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point
from testcases.cu_pass.features.environment.global_parsers import parse_lat_lng, COORDINATES_REGEX
from testcases.cu_pass.features.environment.hooks import ContextSas
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ARBITRARY_COORDINATES, \
    get_arbitrary_coordinates

use_step_matcher('cfparse')


@parse.with_pattern(rf' and center coordinates {COORDINATES_REGEX}')
def parse_optional_coordinates(text: str) -> Point:
    coordinates_text = re.compile(COORDINATES_REGEX).search(text)
    return parse_lat_lng(text=coordinates_text[0])


register_type(OptionalCoordinates=parse_optional_coordinates)


@dataclass
class ContextArea(ContextSas):
    area: AreaCircle


@step("a circular area with a radius of {radius_in_kilometers:Integer} km{coordinates:OptionalCoordinates?}")
def step_impl(context: ContextArea, radius_in_kilometers: int, coordinates: Optional[Point]):
    """
    Args:
        context (behave.runner.Context):
    """
    context.area = AreaCircle(
        center_coordinates=coordinates or get_arbitrary_coordinates(),
        radius_in_kilometers=radius_in_kilometers
    )
