import random
from dataclasses import dataclass
from functools import partial

from behave import *
from behave.api.async_step import async_run_until_complete

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import AggregateInterferenceMonteCarloCalculator, \
    InterferenceParameters
from dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.parameter_finder import ParameterFinder
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.population_retriever.population_retriever_straight_file import PopulationRetrieverStraightFile
from dpa_calculator.utilities import get_dpa_center, Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextNeighborhood(ContextResult, ContextDpa):
    interference_threshold: int


@step("an interference_threshold of {interference_threshold:Integer}")
def step_impl(context: ContextNeighborhood, interference_threshold: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.interference_threshold = interference_threshold


@when("the neighborhood radius is calculated")
def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    override_number_of_aps_for_speed_purposes = 50
    override_number_of_iterations_for_speed_purposes = 10
    context.result = AggregateInterferenceMonteCarloCalculator(dpa=context.dpa,
                                                               target_threshold=context.interference_threshold,
                                                               number_of_iterations=override_number_of_iterations_for_speed_purposes).simulate().distance
