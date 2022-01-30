from dataclasses import dataclass
from math import inf
from typing import Callable, List

from behave import *

from cu_pass.dpa_calculator.binary_search.parameter_finder import ParameterFinder
from cu_pass.dpa_calculator.binary_search.binary_search import InputWithReturnedValue
from cu_pass.dpa_calculator.binary_search.shortest_unchanging import ShortestUnchangingInputFinder
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
    def function(x: int):
        if x < 0 or x >= len(result_array):
            return -inf
        else:
            return result_array[x]
    context.function = function


@given("a target of {target:Integer}")
def step_impl(context: ContextBinarySearch, target: int):
    """
    Args:
        context (behave.runner.Context):
        target (str):
    """
    context.target = target


@when("the shortest unchanging algorithm is run with step size {step_size:d}")
def step_impl(context: ContextBinarySearch, step_size: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = ShortestUnchangingInputFinder(function=context.function,
                                                   max_parameter=context.max_input,
                                                   step_size=step_size).find()


@when("the descending binary search algorithm is run with step size {step_size:d}")
def step_impl(context: ContextBinarySearch, step_size: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = ParameterFinder(function=context.function,
                                     target=context.target,
                                     max_parameter=context.max_input,
                                     step_size=step_size).find()


@then("the resulting input should be {expected_input:Integer}")
def step_impl(context: ContextBinarySearch, expected_input: int):
    assert context.result.input == expected_input, f'{context.result.input} != {expected_input}'


@step("the resulting return value should be {expected_value:Number}")
def step_impl(context: ContextBinarySearch, expected_value: float):
    assert context.result.returned_value == expected_value, f'{context.result.returned_value} != {expected_value}'
