import random
from dataclasses import dataclass
from math import isclose
from typing import List, Set

from behave import *
from behave import runner

from dpa_calculator.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import HIGH_FREQ_COCH, LOW_FREQ_COCH
from testcases.cu_pass.features.steps.dpa_parameters.environment.parsers import CBSD_A_INDICATOR, REGION_TYPE_RURAL, \
    get_cbsd_ap


@dataclass
class ContextMonteCarlo(runner.Context):
    dpa: Dpa
    dpa_test_zone: AreaCircle
    grants: List[CbsdGrantInfo]
    interference: float


@given("an antenna at {dpa:Dpa}")
def step_impl(context: ContextMonteCarlo, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa = dpa


@step("an exclusion zone distance of {distance:Integer} km")
def step_impl(context: ContextMonteCarlo, distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa_test_zone = AreaCircle(
        radius_in_kilometers=context.dpa.neighbor_distances[0],
        center_coordinates=Point.from_shapely(point_shapely=context.dpa.geometry.centroid)
    )


@step("{number_of_aps:Integer} APs")
def step_impl(context: ContextMonteCarlo, number_of_aps: int):
    """
    Args:
        context (behave.runner.Context):
    """
    random.seed(0)
    number_of_indoor_aps = int(number_of_aps * 0.99)
    distributed_aps = PointDistributor(distribution_area=context.dpa_test_zone).distribute_points(number_of_points=number_of_aps)
    indoor_aps = distributed_aps[:number_of_indoor_aps]
    outdoor_aps = distributed_aps[number_of_indoor_aps:]
    aps = [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=True, location=location) for location in indoor_aps] \
          + [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=False, location=location) for location in outdoor_aps]
    grants = [ap.to_grant() for ap in aps]
    inband_channel = next(channel for channel in context.dpa._channels if channel[0] * 1e6 >= LOW_FREQ_COCH and channel[1] * 1e6 <= HIGH_FREQ_COCH)
    for index, grant in enumerate(grants):
        grants[index] = grant._replace(low_frequency=inband_channel[0] * 1e6, high_frequency=(inband_channel[0] + 10) * 1e6)
    context.grants = grants


@when("a monte carlo simulation of {number_of_iterations:Integer} iterations of the aggregate interference is run")
def step_impl(context: ContextMonteCarlo, number_of_iterations: int):
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
def step_impl(context: ContextMonteCarlo, max_interference: float):
    """
    Args:
        context (behave.runner.Context):
    """
    assert isclose(context.interference, max_interference, abs_tol=1e-5), f'{context.interference} != {max_interference}'
