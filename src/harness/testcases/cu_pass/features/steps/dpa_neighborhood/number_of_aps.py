from dataclasses import dataclass

from behave import *

from dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from testcases.cu_pass.features.environment.hooks import ContextSas


@dataclass
class ContextNumberOfAps(ContextSas):
    simulation_population: int


@step("simulation population of {population:Integer}")
def step_impl(context: ContextNumberOfAps, population: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.simulation_population = population


@then("the number of APs for simulation is {expected_number_of_aps:Integer}")
def step_impl(context: ContextNumberOfAps, expected_number_of_aps: float):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_aps_calculator = NumberOfApsCalculatorGroundBased(simulation_population=context.simulation_population)
    assert number_of_aps_calculator.get_number_of_aps() == expected_number_of_aps
