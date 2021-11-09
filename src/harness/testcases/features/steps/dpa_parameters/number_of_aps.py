from dataclasses import dataclass

from behave import runner
from math import isclose

from behave import *

from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class ContextNumberOfAps(runner.Context):
    city_population: int
    dpa: Dpa
    simulation_population_ratio: float


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
    context.simulation_population_ratio = population / context.city_population


@then("the number of APs for simulation is {expected_number_of_aps:Number}")
def step_impl(context: ContextNumberOfAps, expected_number_of_aps: float):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_aps = (context.city_population * 0.4 * context.simulation_population_ratio * 0.2 * 1) / 20
    assert isclose(number_of_aps, expected_number_of_aps)
