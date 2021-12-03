from dataclasses import dataclass
from functools import partial
from typing import Type

from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum import \
    AggregateInterferenceCalculatorWinnforum
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator, get_aggregate_interference_monte_carlo_calculator
from dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from dpa_calculator.population_retriever.population_retriever_region_type import PopulationRetrieverRegionType
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextNeighborhood(ContextResult, ContextDpa):
    interference_threshold: int
    monte_carlo_runner: Type[AggregateInterferenceMonteCarloCalculator]


@step("an interference_threshold of {interference_threshold:Integer}")
def step_impl(context: ContextNeighborhood, interference_threshold: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.interference_threshold = interference_threshold


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
        'census': PopulationRetrieverCensus,
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


@when("the neighborhood radius is calculated")
def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    override_number_of_aps_for_speed_purposes = 50
    override_number_of_iterations_for_speed_purposes = 10
    context.result = context.monte_carlo_runner(dpa=context.dpa,
                                                target_threshold=context.interference_threshold,
                                                number_of_iterations=override_number_of_iterations_for_speed_purposes).simulate().distance
