from dataclasses import dataclass

from behave import runner
from math import isclose

from behave import *

from dpa_calculator.dpa_calculator import NumberOfApsCalculatorGroundBased
from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class ContextNumberOfAps(runner.Context):
    city_population: int
    dpa: Dpa
    simulation_population: int


@given("a city population of {population:Integer}")
def step_impl(context: ContextNumberOfAps, population: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.city_population = population


@step("the radar at {dpa:Dpa}")
def step_impl(context: ContextNumberOfAps, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa = dpa


@step("simulation population area of {population:Integer}")
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
    number_of_aps_calculator = NumberOfApsCalculatorGroundBased(city_population=context.city_population,
                                                                simulation_population=context.simulation_population)
    assert number_of_aps_calculator.number_of_aps == expected_number_of_aps
