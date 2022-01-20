from dataclasses import dataclass
from typing import Iterable, List, Optional

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdTypes
from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdCategories
from cu_pass.dpa_calculator.cbsds_creator.utilities import get_cbsds_creator
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.utilities import get_dpa_center
from testcases.cu_pass.features.environment.global_parsers import INTEGER_REGEX, parse_integer
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType, \
    get_arbitrary_coordinates
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_cbsd_category import \
    parse_cbsd_category

use_step_matcher('re')


ARBITRARY_ODD_NUMBER_OF_APS = 1001
ARBITRARY_RADIUS = 150

ACCESS_POINT_OR_USER_EQUIPMENT_REGEX = rf'({CbsdTypes.AP.name}|{CbsdTypes.UE.name})'


def parse_is_user_equipment(text: str) -> bool:
    return CbsdTypes[text] == CbsdTypes.UE


@dataclass
class ContextCbsdCreation(ContextArea, ContextDpa, ContextRegionType):
    bearings: List[float]
    cbsds: List[Cbsd]


def _parse_cbsd_category(cbsd_category_input: str) -> Iterable[CbsdCategories]:
    return [parse_cbsd_category(cbsd_category_input=cbsd_category_input)] if cbsd_category_input else CbsdCategories


@when(f"(Category (?P<cbsd_category>[AB]))? ?(?P<is_user_equipment>{ACCESS_POINT_OR_USER_EQUIPMENT_REGEX})? ?CBSDs (for (?P<number_of_aps>{INTEGER_REGEX}) APs)? ?for the Monte Carlo simulation are created")
def step_impl(context: ContextCbsdCreation, *args, cbsd_category: str, number_of_aps: Optional[str], is_user_equipment: Optional[str]):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsd_category = CbsdCategories.B if cbsd_category == CbsdCategories.B.name else CbsdCategories.A
    number_of_aps = parse_integer(text=number_of_aps) if number_of_aps else ARBITRARY_ODD_NUMBER_OF_APS
    is_user_equipment = is_user_equipment and parse_is_user_equipment(text=is_user_equipment)
    dpa_zone = getattr(context, 'area', _create_area(context=context))
    cbsds_creator = get_cbsds_creator(cbsd_category=cbsd_category,
                                      dpa_zone=dpa_zone,
                                      is_user_equipment=is_user_equipment,
                                      number_of_aps=number_of_aps)
    cbsds_with_bearings = cbsds_creator.create()
    context.bearings = cbsds_with_bearings.bearings
    context.cbsds = cbsds_with_bearings.cbsds


def _create_area(context: ContextCbsdCreation) -> AreaCircle:
    dpa = getattr(context, 'dpa', None)
    center_coordinates = getattr(context, 'antenna_coordinates', None) \
        or dpa and get_dpa_center(dpa=dpa) \
        or get_arbitrary_coordinates()
    return AreaCircle(center_coordinates=center_coordinates,
                      radius_in_kilometers=ARBITRARY_RADIUS)
