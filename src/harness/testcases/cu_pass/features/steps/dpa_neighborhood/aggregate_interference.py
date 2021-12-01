import random
from dataclasses import dataclass

from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import AggregateInterferenceMonteCarloCalculator, \
    InterferenceParameters
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utilities import get_dpa_center
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')

DEFAULT_SIMULATION_RADIUS = 500


@dataclass
class ContextAggregateInterference(InterferenceParameters, ContextResult, ContextDpa):
    pass


@step("an exclusion zone distance of {distance:Integer} km")
def step_impl(context: ContextAggregateInterference, distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa_test_zone = AreaCircle(
        radius_in_kilometers=DEFAULT_SIMULATION_RADIUS,
        center_coordinates=get_dpa_center(dpa=context.dpa)
    )


@step("{number_of_aps:Integer} APs")
def step_impl(context: ContextAggregateInterference, number_of_aps: int):
    """
    Args:
        context (behave.runner.Context):
    """
    random.seed(0)
    context.number_of_aps = number_of_aps


@when("a monte carlo simulation of {number_of_iterations:Integer} iterations for the aggregate interference is run")
def step_impl(context: ContextAggregateInterference, number_of_iterations: int):
    """
    Args:
        context (behave.runner.Context):
    """
    simulation_result = AggregateInterferenceMonteCarloCalculator(interference_parameters=context, number_of_iterations=number_of_iterations).simulate()
    context.result = simulation_result.interference_max
