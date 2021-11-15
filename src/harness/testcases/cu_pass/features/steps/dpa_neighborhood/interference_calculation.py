import random
from dataclasses import dataclass

from math import isclose

from behave import *

from dpa_calculator.aggregate_interference_monte_carlo_calculator import AggregateInterferenceMonteCarloCalculator, \
    InterferenceParameters
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point
from reference_models.dpa.dpa_mgr import Dpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult


@dataclass
class ContextAggregateInterference(InterferenceParameters, ContextResult):
    pass


@given("an antenna at {dpa:Dpa}")
def step_impl(context: ContextAggregateInterference, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa = dpa


@step("an exclusion zone distance of {distance:Integer} km")
def step_impl(context: ContextAggregateInterference, distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa_test_zone = AreaCircle(
        radius_in_kilometers=context.dpa.neighbor_distances[0],
        center_coordinates=Point.from_shapely(point_shapely=context.dpa.geometry.centroid)
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
    context.result = AggregateInterferenceMonteCarloCalculator(interference_parameters=context, number_of_iterations=number_of_iterations).simulate()


@then("the result should be {max_interference:Number}")
def step_impl(context: ContextAggregateInterference, max_interference: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert isclose(context.result, max_interference, abs_tol=1e-4), f'{context.result} != {max_interference}'
