from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher("parse")


@then("transmitter insertion losses for {is_indoor:IsIndoor} APs should be {expected_power:Integer} dB")
def step_impl(context: ContextCbsdInterference, is_indoor: str, expected_power: int, **kwargs):
    """
    Args:
        context (behave.runner.Context):
    """
    interference_contributions = [context.interference_components[cbsd_number]
                                  for cbsd_number, cbsd in enumerate(context.cbsds)
                                  if cbsd.is_indoor == is_indoor]
    assert all(contribution.loss_transmitter == expected_power for contribution in interference_contributions)


@step("transmitter insertion losses for UEs should be {expected_power:Integer} dB")
def step_impl(context: ContextCbsdInterference, expected_power: int):
    """
    Args:
        context (behave.runner.Context):
    """
    assert all(contribution.loss_transmitter == expected_power for contribution in context.interference_components)
