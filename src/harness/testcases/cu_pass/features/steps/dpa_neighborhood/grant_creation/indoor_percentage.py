from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher('parse')


@then("{expected_indoor_percentage:Number} of the grants should be indoors")
def step_impl(context: ContextGrantCreation, expected_indoor_percentage: float):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_percentage = sum(1 for grant in context.grants if grant.indoor_deployment) / len(context.grants)
    assert indoor_percentage == expected_indoor_percentage, f'{indoor_percentage} != {expected_indoor_percentage}'
