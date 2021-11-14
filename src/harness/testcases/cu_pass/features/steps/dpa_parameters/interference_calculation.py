import random
from dataclasses import dataclass
from math import isclose
from typing import List

from behave import *
from behave import runner

from dpa_calculator.grants_creator import GrantsCreator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import HIGH_FREQ_COCH, LOW_FREQ_COCH


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


@when("a monte carlo simulation of {number_of_iterations:Integer} iterations of the aggregate interference is run")
def step_impl(context: ContextAggregateInterference, number_of_iterations: int):
    """
    Args:
        context (behave.runner.Context):
    """
    inband_channel = next(channel for channel in context.dpa._channels if channel[0] * 1e6 >= LOW_FREQ_COCH and channel[1] * 1e6 <= HIGH_FREQ_COCH)
    for index, grant in enumerate(context.grants):
        context.grants[index] = grant._replace(low_frequency=inband_channel[0] * 1e6, high_frequency=(inband_channel[0] + 10) * 1e6)
    context.dpa.nbor_lists = [set(context.grants) for _ in context.dpa.nbor_lists]
    context.interference = context.dpa.CalcKeepListInterference(channel=inband_channel, num_iter=number_of_iterations)[0]


@then("the max aggregate interference is {max_interference:Number}")
def step_impl(context: ContextAggregateInterference, max_interference: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert isclose(context.interference, max_interference, abs_tol=1e-5), f'{context.interference} != {max_interference}'
