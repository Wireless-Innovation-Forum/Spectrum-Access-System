from dataclasses import dataclass
from typing import List, Optional

from behave import *

from cu_pass.dpa_calculator.helpers.list_distributor import FractionalDistribution
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher("cfparse")


@dataclass
class ContextTransmissionPower(ContextCbsdCreation):
    pass


@then("the {is_indoor:IsIndoor?}antenna maximum EIRPs should be {expected_powers:FractionalDistribution} dBm")
def step_impl(context: ContextTransmissionPower, is_indoor: Optional[bool], expected_powers: List[FractionalDistribution]):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsds = context.cbsds if is_indoor is None else (cbsd for cbsd in context.cbsds if cbsd.is_indoor == is_indoor)
    max_eirps = [cbsd.eirp_maximum for cbsd in cbsds]
    for expected_power in expected_powers:
        expected_power.assert_data_matches_distribution(data=max_eirps)
