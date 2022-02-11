from dataclasses import dataclass
from typing import Callable, Iterator, List

from behave import *

from cu_pass.dpa_calculator.utilities import run_monte_carlo_simulation
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextMonteCarlo(ContextResult):
    functions_to_run: List[Callable[[], float]]
    number_of_iterations: int
    result: float


@given("functions whose results return the next element of {function_results_list:NumberListList} each time it runs")
def step_impl(context: ContextMonteCarlo, function_results_list: List[List[float]]):
    """
    Args:
        context (behave.runner.Context):
    """
    context.number_of_iterations = min(len(function_results) for function_results in function_results_list)
    result_iterators = [(result for result in function_results) for function_results in function_results_list]
    context.functions_to_run = [function_creator(result_iterator=result_iterator) for result_iterator in result_iterators]


def function_creator(result_iterator: Iterator) -> Callable[[], float]:
    return lambda: next(result_iterator)


@when("a monte carlo simulation of the function is run for the {percentile:Number} percentile")
def step_impl(context: ContextMonteCarlo, percentile: float):
    """
    Args:
        context (behave.runner.Context):
    """
    context.result = run_monte_carlo_simulation(functions_to_run=context.functions_to_run,
                                                number_of_iterations=context.number_of_iterations,
                                                percentile=percentile)


@then("the simulation results should be {expected_results:NumberList}")
def step_impl(context: ContextMonteCarlo, expected_results: List[float]):
    """
    Args:
        context (behave.runner.Context):
    """
    assert context.result == expected_results, f'{context.result} != {expected_results}'
