from math import isclose

from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher('parse')


@then("{expected_indoor_percentage:Number} of the grants should be indoors")
def step_impl(context: ContextCbsdCreation, expected_indoor_percentage: float):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_percentage = sum(1 for cbsd in context.cbsds if cbsd.is_indoor) / len(context.cbsds)
    assert isclose(indoor_percentage, expected_indoor_percentage, abs_tol=.01), f'{indoor_percentage} != {expected_indoor_percentage}'
