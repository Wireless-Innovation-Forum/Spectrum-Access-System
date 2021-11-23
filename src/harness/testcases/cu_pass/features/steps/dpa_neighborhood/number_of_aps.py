from dataclasses import dataclass

from behave import *

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from dpa_calculator.utils import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult


@dataclass
class ContextNumberOfAps(ContextResult):
    antenna_coordinates: Point
    simulation_population: int


@step("a {region_type} location")
def step_impl(context: ContextNumberOfAps, region_type: str):
    """
    Args:
        context (behave.runner.Context):
        region_type (str):
    """
    region_type_to_arbitrary_coordinates = {
        REGION_TYPE_RURAL: Point(latitude=37.779704, longitude=-122.417747),
        REGION_TYPE_SUBURBAN: Point(latitude=37.753571, longitude=-122.44803),
        REGION_TYPE_URBAN: Point(latitude=37.781941, longitude=-122.404195)
    }
    context.antenna_coordinates = region_type_to_arbitrary_coordinates[region_type.upper()]


@step("simulation population of {population:Integer}")
def step_impl(context: ContextNumberOfAps, population: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.simulation_population = population


@when("the number of APs for simulation is calculated")
def step_impl(context: ContextNumberOfAps):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_aps_calculator = NumberOfApsCalculatorShipborne(
        center_coordinates=context.antenna_coordinates,
        simulation_population=context.simulation_population
    )
    context.result = number_of_aps_calculator.get_number_of_aps()
