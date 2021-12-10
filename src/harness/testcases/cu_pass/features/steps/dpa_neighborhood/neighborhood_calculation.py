from dataclasses import dataclass
from functools import partial
from typing import Type

from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum import \
    AggregateInterferenceCalculatorWinnforum
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator
from dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from dpa_calculator.population_retriever.population_retriever_region_type import PopulationRetrieverRegionType
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextNeighborhood(ContextResult, ContextDpa):
    monte_carlo_runner: Type[AggregateInterferenceMonteCarloCalculator]
    number_of_iterations: int
    simulation_area_radius: int


@step("{organization} interference")
def step_impl(context: ContextNeighborhood, organization: str):
    map = {
        'NTIA': AggregateInterferenceCalculatorNtia,
        'WinnForum': AggregateInterferenceCalculatorWinnforum
    }
    context.monte_carlo_runner = partial(context.monte_carlo_runner,
                                         aggregate_interference_calculator_class=map[organization])


@step("population by {population_type}")
def step_impl(context: ContextNeighborhood, population_type: str):
    map = {
        'census radius': PopulationRetrieverCensus,
        'region type': PopulationRetrieverRegionType
    }
    context.monte_carlo_runner = partial(context.monte_carlo_runner,
                                         population_retriever_class=map[population_type])


@step("number of APs using {number_of_aps_type} analysis")
def step_impl(context: ContextNeighborhood, number_of_aps_type: str):
    map = {
        'ground based': NumberOfApsCalculatorGroundBased,
        'shipborne': NumberOfApsCalculatorShipborne
    }
    context.monte_carlo_runner = partial(context.monte_carlo_runner,
                                         number_of_aps_calculator_class=map[number_of_aps_type])


@step("a simulation area radius of {simulation_area_radius:Integer}")
def step_impl(context: ContextNeighborhood, simulation_area_radius: int):
    context.simulation_area_radius = simulation_area_radius


@step("{number_of_iterations:Integer} monte carlo iterations")
def step_impl(context: ContextNeighborhood, number_of_iterations: int):
    context.number_of_iterations = number_of_iterations


@when("the neighborhood radius is calculated")
def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    simulation_results = context.monte_carlo_runner(dpa=context.dpa,
                                                    number_of_iterations=context.number_of_iterations,
                                                    simulation_area_radius_in_kilometers=context.simulation_area_radius).simulate()
    context.result = simulation_results.distance
