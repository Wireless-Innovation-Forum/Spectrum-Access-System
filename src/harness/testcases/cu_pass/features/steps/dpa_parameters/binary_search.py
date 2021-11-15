from dataclasses import dataclass
from typing import Callable, List

from behave import *

from dpa_calculator.parameter_finder import ParameterFinder
from testcases.cu_pass.features.steps.dpa_parameters.common_steps.result import ContextResult


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
    context.function = lambda x: result_array[x]


@given("a target of {target:Integer}")
def step_impl(context: ContextBinarySearch, target: int):
    """
    Args:
        context (behave.runner.Context):
        target (str):
    """
    context.target = target


@when("the algorithm is run")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = ParameterFinder(function=context.function, target=context.target, max_parameter=context.max_input).find()
