from dataclasses import dataclass
from typing import Callable, List

from behave import *

from dpa_calculator.parameter_finder import InputWithReturnedValue, ParameterFinder
from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher('parse')


@dataclass
class ContextBinarySearch(ContextSas):
    function: Callable[[int], float]
    result: InputWithReturnedValue
    target: int


@given("a function whose output is the element of array {result_array:NumberList} at the given index")
def step_impl(context: ContextBinarySearch, result_array: List[float]):
    """
    Args:
        context (behave.runner.Context):
    """
    context.max_input = len(result_array) - 1
    def function(x: int): return result_array[x]
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
def step_impl(context: ContextBinarySearch):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = ParameterFinder(function=context.function, target=context.target, max_parameter=context.max_input).find()


@then("the resulting input should be {expected_input:Integer}")
def step_impl(context: ContextBinarySearch, expected_input: int):
    assert context.result.input == expected_input, f'{context.result.input} != {expected_input}'


@step("the resulting return value should be {expected_value:Number}")
def step_impl(context: ContextBinarySearch, expected_value: float):
    assert context.result.returned_value == expected_value, f'{context.result.returned_value} != {expected_value}'
