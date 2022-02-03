from dataclasses import dataclass

from behave import *

from testcases.cu_pass.dpa_calculator.features.environment.hooks import ContextSas

use_step_matcher('parse')


@dataclass
class ContextResult(ContextSas):
    result: float


@then("the result should be {expected_result:Number}")
def step_impl(context: ContextResult, expected_result: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert context.result == expected_result, f'{context.result} != {expected_result}'
