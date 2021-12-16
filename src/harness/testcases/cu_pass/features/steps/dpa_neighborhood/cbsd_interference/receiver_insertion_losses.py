from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher("parse")


@then("all receiver insertion losses should be {expected_power:Integer} dB")
def step_impl(context: ContextCbsdInterference, expected_power: int):
    assert all(contributions.loss_receiver == expected_power for contributions in context.interference_components)
