from dataclasses import dataclass

from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher("parse")


@dataclass
class ContextGains(ContextGrantCreation):
    pass


@then("the antenna gains should be {expected_height:Integer} meters")
def step_impl(context: ContextGains, expected_height: int):
    """
    Args:
        context (behave.runner.Context):
    """
    assert all(grant.antenna_gain == expected_height for grant in context.grants)
