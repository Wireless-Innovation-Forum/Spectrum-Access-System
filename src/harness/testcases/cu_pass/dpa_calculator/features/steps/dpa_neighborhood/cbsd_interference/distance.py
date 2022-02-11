from math import isclose

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd
from cu_pass.dpa_calculator.point_distributor import AreaCircle, PointDistributor
from cu_pass.dpa_calculator.utilities import get_dpa_center
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ARBITRARY_ANTENNA_HEIGHT_IN_METERS, ARBITRARY_EIRP_MAXIMUM, ContextCbsdInterference
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher("parse")


@given("a CBSD {distance:Integer} km away from the DPA")
def step_impl(context: ContextCbsdInterference, distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    assign_arbitrary_dpa(context=context)
    point_distributor = PointDistributor(distribution_area=AreaCircle(center_coordinates=get_dpa_center(dpa=context.dpa), radius_in_kilometers=distance), minimum_distance=distance)
    cbsd_location_with_bearing = point_distributor.distribute_points(number_of_points=1)[0]
    context.cbsds = [Cbsd(eirp_maximum=ARBITRARY_EIRP_MAXIMUM, height_in_meters=ARBITRARY_ANTENNA_HEIGHT_IN_METERS, location=cbsd_location_with_bearing.coordinates)]
    context.bearings = [cbsd_location_with_bearing.bearing]


@then("the distance from the antenna should be {expected_distance:Number}")
def step_impl(context: ContextCbsdInterference, expected_distance: float):
    """
    Args:
        context (behave.runner.Context):
    """
    distance = context.interference_components[0].distance_in_kilometers
    assert isclose(distance, expected_distance), f'{distance} != {expected_distance}'
