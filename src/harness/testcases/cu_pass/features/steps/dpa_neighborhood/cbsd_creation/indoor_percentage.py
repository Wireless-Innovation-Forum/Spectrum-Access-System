from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher('parse')


@then("{expected_indoor_percentage:Number} of the grants should be indoors")
def step_impl(context: ContextCbsdCreation, expected_indoor_percentage: float):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_percentage = sum(1 for cbsd in context.cbsds if cbsd.is_indoor) / len(context.cbsds)
    assert round(indoor_percentage, 2) == expected_indoor_percentage, f'{indoor_percentage} != {expected_indoor_percentage}'
