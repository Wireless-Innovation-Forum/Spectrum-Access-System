from dataclasses import dataclass
from typing import Callable, List

from behave import *
from behave.api.async_step import async_run_until_complete

from dpa_calculator.parameter_finder import ParameterFinder
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextBinarySearch(ContextResult):
    function: Callable[[int], float]
    target: int


@given("a function whose output is the element of array {result_array:NumberList} at the given index")
def step_impl(context: ContextBinarySearch, result_array: List[float]):
    """
    Args:
        context (behave.runner.Context):
    """
    context.max_input = len(result_array) - 1
    async def function(x: int): return result_array[x]
    context.function = function


@given("a target of {target:Integer}")
def step_impl(context: ContextBinarySearch, target: int):
    """
    Args:
        context (behave.runner.Context):
        target (str):
    """
    context.target = target


@when("the algorithm is run")
@async_run_until_complete
async def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = await ParameterFinder(function=context.function, target=context.target, max_parameter=context.max_input).find()
