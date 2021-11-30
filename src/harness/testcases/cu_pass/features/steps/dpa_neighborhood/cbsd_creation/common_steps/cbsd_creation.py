from dataclasses import dataclass
from enum import auto, Enum
from typing import List

import parse
from behave import *

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.grants_creator.utilities import get_grants_creator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utilities import Point
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType, \
    get_arbitrary_coordinates

use_step_matcher('cfparse')


ARBITRARY_ODD_NUMBER_OF_APS = 1001
ARBITRARY_RADIUS = 150


class CbsdTypes(Enum):
    AP = auto()
    UE = auto()


@parse.with_pattern(rf'({CbsdTypes.AP.name}|{CbsdTypes.UE.name}) ')
def parse_is_user_equipment(text: str) -> bool:
    return CbsdTypes[text] == CbsdTypes.UE


register_type(IsUserEquipment=parse_is_user_equipment)


@dataclass
class ContextCbsdCreation(ContextArea, ContextDpa, ContextRegionType):
    cbsds: List[Cbsd]


@when("{is_user_equipment:IsUserEquipment?}CBSDs for the Monte Carlo simulation are created")
def step_impl(context: ContextCbsdCreation, is_user_equipment: bool = False):
    """
    Args:
        context (behave.runner.Context):
    """
    dpa_zone = getattr(context, 'area', _create_area(context=context))
    grants_creator = get_grants_creator(dpa_zone=dpa_zone, is_user_equipment=is_user_equipment, number_of_aps=ARBITRARY_ODD_NUMBER_OF_APS)
    context.cbsds = grants_creator.create()


def _create_area(context: ContextCbsdCreation) -> AreaCircle:
    dpa = getattr(context, 'dpa', None)
    center_coordinates = getattr(context, 'antenna_coordinates', None) \
        or dpa and Point.from_shapely(point_shapely=dpa.geometry.centroid) \
        or get_arbitrary_coordinates()
    return AreaCircle(center_coordinates=center_coordinates,
                      radius_in_kilometers=ARBITRARY_RADIUS)
