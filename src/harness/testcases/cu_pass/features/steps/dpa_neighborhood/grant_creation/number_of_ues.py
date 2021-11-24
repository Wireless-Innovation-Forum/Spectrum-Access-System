from dataclasses import dataclass

from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher("parse")


@dataclass
class ContextNumberOfUes(ContextGrantCreation):
    pass


@then("there should be {number_of_ues_per_ap:Integer} times as many as if AP grants were created")
def step_impl(context: ContextNumberOfUes, number_of_ues_per_ap: int):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_ue_grants = len(context.grants)
    context.execute_steps(u'When AP grants for the Monte Carlo simulation are created')
    number_of_ap_grants = len(context.grants)
    assert number_of_ue_grants == number_of_ues_per_ap * number_of_ap_grants
