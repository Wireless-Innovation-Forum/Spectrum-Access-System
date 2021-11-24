from dataclasses import dataclass
from typing import Optional

import parse
from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher("cfparse")

INDOOR_STRING = 'indoor'
OUTDOOR_STRING = 'outdoor'


@parse.with_pattern(rf'({INDOOR_STRING}|{OUTDOOR_STRING}) ')
def parse_is_indoor(text: str) -> bool:
    return text.strip() == INDOOR_STRING


register_type(IsIndoor=parse_is_indoor)


@dataclass
class ContextTransmissionPower(ContextGrantCreation):
    pass


@then("the {is_indoor:IsIndoor?}antenna EIRPs should be {expected_power:Integer} dBm")
def step_impl(context: ContextTransmissionPower, is_indoor: Optional[bool], expected_power: int):
    """
    Args:
        context (behave.runner.Context):
    """
    grants = context.grants if is_indoor is None else (grant for grant in context.grants if grant.indoor_deployment == is_indoor)
    assert all(grant.max_eirp == expected_power for grant in grants)
