from dataclasses import dataclass
from typing import Callable

from behave import *

from dpa_calculator.utilities import run_monte_carlo_simulation
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextMonteCarlo(ContextResult):
    function_to_run: Callable[[], float]
    result: float


@given("a function whose results return the next element of [1,2,3,4,5] each time it runs")
def step_impl(context: ContextMonteCarlo):
    """
    Args:
        context (behave.runner.Context):
    """
    function_results = (i for i in range(1, 6))
    context.function_to_run = lambda: next(function_results)


@when("a monte carlo simulation of the function is run")
def step_impl(context: ContextMonteCarlo):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_iterations = 5
    context.result = run_monte_carlo_simulation(function_to_run=context.function_to_run, number_of_iterations=number_of_iterations)

