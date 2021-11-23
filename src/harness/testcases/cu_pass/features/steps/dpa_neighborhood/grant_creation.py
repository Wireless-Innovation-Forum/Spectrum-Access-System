from dataclasses import dataclass
from typing import List

from behave import *

from dpa_calculator.grants_creator import GrantsCreator
from dpa_calculator.point_distributor import AreaCircle
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType

ARBITRARY_NUMBER_OF_CBSDS = 1000
ARBITRARY_RADIUS = 150


@dataclass
class ContextGrantCreation(ContextRegionType):
    grants: List[CbsdGrantInfo]


@when("grants for the Monte Carlo simulation are created")
def step_impl(context: ContextGrantCreation):
    """
    Args:
        context (behave.runner.Context):
    """
    zpa_zone = AreaCircle(center_coordinates=context.antenna_coordinates, radius_in_kilometers=ARBITRARY_RADIUS)
    context.grants = GrantsCreator(dpa_zone=zpa_zone,
                                   number_of_cbsds=ARBITRARY_NUMBER_OF_CBSDS).create()


@then("{expected_indoor_percentage:Number} of the grants should be indoors")
def step_impl(context: ContextGrantCreation, expected_indoor_percentage: float):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_percentage = sum(1 for grant in context.grants if grant.indoor_deployment) / len(context.grants)
    assert indoor_percentage == expected_indoor_percentage, f'{indoor_percentage} != {expected_indoor_percentage}'
