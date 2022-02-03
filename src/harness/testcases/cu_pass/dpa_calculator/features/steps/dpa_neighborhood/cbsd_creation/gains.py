from dataclasses import dataclass

from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher("parse")


@dataclass
class ContextGains(ContextCbsdCreation):
    pass


@then("the antenna gains should be {expected_height:Integer} meters")
def step_impl(context: ContextGains, expected_height: int):
    """
    Args:
        context (behave.runner.Context):
    """
    assert all(grant.gain == expected_height for grant in context.cbsds)
