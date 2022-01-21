from dataclasses import dataclass
from typing import Iterable, List, Optional

from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.cbsd_deployer import \
    CbsdDeployer
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_APS_FOR_POPULATION_TYPE
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.utilities import get_dpa_center, Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType, \
    get_arbitrary_coordinates
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_cbsd_category import \
    parse_cbsd_category

use_step_matcher('re')


ARBITRARY_ODD_NUMBER_OF_APS = 1001

ACCESS_POINT_OR_USER_EQUIPMENT_REGEX = rf'({CbsdTypes.AP.name}|{CbsdTypes.UE.name})'


def parse_is_user_equipment(text: str) -> bool:
    return CbsdTypes[text] == CbsdTypes.UE


@dataclass
class ContextCbsdCreation(ContextArea, ContextDpa, ContextRegionType):
    bearings: List[float]
    cbsds: List[Cbsd]


def _parse_cbsd_category(cbsd_category_input: str) -> Iterable[CbsdCategories]:
    return [parse_cbsd_category(cbsd_category_input=cbsd_category_input)] if cbsd_category_input else CbsdCategories


@when(f"(category (?P<cbsd_category>[AB]))? ?(?P<is_user_equipment>{ACCESS_POINT_OR_USER_EQUIPMENT_REGEX})? ?CBSDs for the Monte Carlo simulation are created")
def cbsd_creation_step(context: ContextCbsdCreation, *args,
                       cbsd_category: Optional[str] = None,
                       is_user_equipment: Optional[str] = None,
                       number_of_aps: Optional[NUMBER_OF_APS_FOR_POPULATION_TYPE] = None):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsd_categories = _parse_cbsd_category(cbsd_category_input=cbsd_category)
    is_user_equipment = is_user_equipment and parse_is_user_equipment(text=is_user_equipment)
    context.center_coordinates = _get_center_coordinates(context=context)

    number_of_aps_per_category = number_of_aps or {category: ARBITRARY_ODD_NUMBER_OF_APS for category in cbsd_categories}
    cbsds_with_bearings = CbsdDeployer(center=context.center_coordinates,
                                       is_user_equipment=is_user_equipment,
                                       cbsd_deployment_options=CbsdDeploymentOptions(
                                           number_of_aps=number_of_aps_per_category,
                                       )).deploy()

    context.bearings = cbsds_with_bearings.bearings
    context.cbsds = cbsds_with_bearings.cbsds


def _get_center_coordinates(context: ContextCbsdCreation) -> Point:
    dpa = getattr(context, 'dpa', None)
    return getattr(context, 'area', None) \
        or getattr(context, 'antenna_coordinates', None) \
        or dpa and get_dpa_center(dpa=dpa) \
        or get_arbitrary_coordinates()
