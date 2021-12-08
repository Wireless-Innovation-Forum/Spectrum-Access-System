from dataclasses import dataclass
from typing import Optional

from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher("cfparse")


@dataclass
class ContextTransmissionPower(ContextCbsdCreation):
    pass


@then("the {is_indoor:IsIndoor?}antenna maximum EIRPs should be {expected_power:Number} dBm")
def step_impl(context: ContextTransmissionPower, is_indoor: Optional[bool], expected_power: int):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsds = context.cbsds if is_indoor is None else (cbsd for cbsd in context.cbsds if cbsd.is_indoor == is_indoor)
    assert all(cbsd.eirp_maximum == expected_power for cbsd in cbsds)
