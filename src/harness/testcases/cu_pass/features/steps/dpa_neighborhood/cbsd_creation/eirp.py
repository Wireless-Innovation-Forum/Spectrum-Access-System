from dataclasses import dataclass
from typing import Optional

import parse
from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher("cfparse")

INDOOR_STRING = 'indoor'
OUTDOOR_STRING = 'outdoor'


@parse.with_pattern(rf'({INDOOR_STRING}|{OUTDOOR_STRING}) ')
def parse_is_indoor(text: str) -> bool:
    return text.strip() == INDOOR_STRING


register_type(IsIndoor=parse_is_indoor)


@dataclass
class ContextTransmissionPower(ContextCbsdCreation):
    pass


@then("the {is_indoor:IsIndoor?}antenna EIRPs should be {expected_power:Integer} dBm")
def step_impl(context: ContextTransmissionPower, is_indoor: Optional[bool], expected_power: int):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsds = context.cbsds if is_indoor is None else (cbsd for cbsd in context.cbsds if cbsd.is_indoor == is_indoor)
    assert all(cbsd.eirp == expected_power for cbsd in cbsds)
