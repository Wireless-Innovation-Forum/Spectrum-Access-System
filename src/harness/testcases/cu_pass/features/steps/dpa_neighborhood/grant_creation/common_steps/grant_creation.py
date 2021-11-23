from dataclasses import dataclass
from typing import List

from behave import *

from dpa_calculator.grants_creator import GrantsCreator
from dpa_calculator.point_distributor import AreaCircle
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType

use_step_matcher('parse')


ARBITRARY_NUMBER_OF_CBSDS = 1000
ARBITRARY_RADIUS = 150


@dataclass
class ContextGrantCreation(ContextArea, ContextRegionType):
    grants: List[CbsdGrantInfo]


@when("grants for the Monte Carlo simulation are created")
def step_impl(context: ContextGrantCreation):
    """
    Args:
        context (behave.runner.Context):
    """
    zpa_zone = getattr(context, 'area', AreaCircle(center_coordinates=context.antenna_coordinates, radius_in_kilometers=ARBITRARY_RADIUS))
    context.grants = GrantsCreator(dpa_zone=zpa_zone,
                                   number_of_cbsds=ARBITRARY_NUMBER_OF_CBSDS).create()
