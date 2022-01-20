from dataclasses import dataclass

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdCategories
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsForPopulation
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import ContextRegionType
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextNumberOfAps(ContextRegionType):
    number_of_aps = NumberOfApsForPopulation
    simulation_population: int


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
    context.number_of_aps = number_of_aps_calculator.get_number_of_aps()


@then("the number of category {cbsd_category:CbsdCategory} APs should be {expected_number:Integer}")
def step_impl(context: ContextNumberOfAps, cbsd_category: CbsdCategories, expected_number: int):
    number_of_aps = context.number_of_aps.category_a if cbsd_category == CbsdCategories.A else context.number_of_aps.category_b
    assert number_of_aps == expected_number, f'{number_of_aps} != {expected_number}'
