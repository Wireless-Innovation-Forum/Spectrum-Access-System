import random
from dataclasses import dataclass
from math import isclose
from typing import List

from behave import *
from behave import runner

from dpa_calculator.aggregate_interference_calculator import AggregateInterferenceCalculator
from dpa_calculator.grants_creator import GrantsCreator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class ContextAggregateInterference(runner.Context):
    dpa: Dpa
    dpa_test_zone: AreaCircle
    grants: List[CbsdGrantInfo]
    interference: float


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
    context.grants = GrantsCreator(dpa=context.dpa, dpa_zone=context.dpa_test_zone, number_of_cbsds=number_of_aps).create()


@when("a monte carlo simulation of {number_of_iterations:Integer} iterations for the aggregate interference is run")
def step_impl(context: ContextAggregateInterference, number_of_iterations: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.interference = AggregateInterferenceCalculator(dpa=context.dpa, grants=context.grants, monte_carlo_iterations=number_of_iterations).calculate()


@then("the max aggregate interference is {max_interference:Number}")
def step_impl(context: ContextAggregateInterference, max_interference: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert isclose(context.interference, max_interference, abs_tol=1e-4), f'{context.interference} != {max_interference}'
