from dataclasses import dataclass

from behave import *
from behave import runner


@dataclass
class ContextResult(runner.Context):
    result: float


@then("the result should be {expected_result:Number}")
def step_impl(context: ContextResult, expected_result: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert context.result == expected_result, f'{context.result} != {expected_result}'
