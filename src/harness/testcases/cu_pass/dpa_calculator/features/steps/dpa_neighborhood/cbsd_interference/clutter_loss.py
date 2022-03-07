from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference
from cu_pass.dpa_calculator.helpers.parsers import NumberRange

use_step_matcher('parse')


@then("clutter loss distribution is within {expected_clutter_loss_range:NumberRange}")
def step_impl(context: ContextCbsdInterference, expected_clutter_loss_range: NumberRange):
    """
    Args:
        context (behave.runner.Context):
        expected_clutter_loss_range (str):
    """
    def is_out_of_range(loss: float) -> bool:
        return loss < expected_clutter_loss_range.low or loss > expected_clutter_loss_range.high
    out_of_range = [interference_components
                    for interference_components in context.interference_components
                    if is_out_of_range(loss=interference_components.loss_clutter)]
    assert not out_of_range, f'Losses {out_of_range} are out of range {expected_clutter_loss_range.low}-{expected_clutter_loss_range.high}'


@step("all losses are equal if and only if {expected_clutter_loss_range:NumberRange} is not a range")
def step_impl(context: ContextCbsdInterference, expected_clutter_loss_range: NumberRange):
    """
    Args:
        context (behave.runner.Context):
        expected_clutter_loss_range (str):
    """
    is_range = expected_clutter_loss_range.low != expected_clutter_loss_range.high
    unique_losses = set(
        interference_components.loss_clutter for interference_components in context.interference_components)
    if is_range:
        assert len(unique_losses) > 1
    else:
        assert len(unique_losses) == 1
