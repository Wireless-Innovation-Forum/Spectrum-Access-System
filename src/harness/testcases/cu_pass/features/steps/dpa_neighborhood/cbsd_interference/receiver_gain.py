from math import isclose
from typing import List

from behave import *

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.dpa.utilities import get_uniform_gain_pattern
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ARBITRARY_ANTENNA_HEIGHT_IN_METERS, ARBITRARY_EIRP_MAXIMUM, ContextCbsdInterference
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher("parse")


@given("azimuth range {azimuth_range:NumberList}")
def step_impl(context: ContextCbsdInterference, azimuth_range: List[float]):
    assign_arbitrary_dpa(context=context)
    context.dpa.azimuth_range = tuple(azimuth_range)


@step("beamwidth {beamwidth:Integer}")
def step_impl(context: ContextCbsdInterference, beamwidth: int):
    context.dpa.beamwidth = beamwidth


@step("a uniform gain pattern")
def step_impl(context: ContextCbsdInterference):
    context.dpa.gain_pattern = get_uniform_gain_pattern()


@step("a CBSD at a location {coordinates:LatLng}")
def step_impl(context: ContextCbsdInterference, coordinates: Point):
    """
    Args:
        context (behave.runner.Context):
    """
    context.cbsds = [Cbsd(eirp_maximum=ARBITRARY_EIRP_MAXIMUM, height_in_meters=ARBITRARY_ANTENNA_HEIGHT_IN_METERS, location=coordinates)]


@then("the receive antenna {gain_or_azimuth} should be {expected_results:NumberList}")
def step_impl(context: ContextCbsdInterference, gain_or_azimuth: str, expected_results: List[float]):
    """
    Args:
        context (behave.runner.Context):
    """
    receiver_gains_per_azimuth = context.interference_components[0].gain_receiver.values()
    attribute_name = 'gain' if gain_or_azimuth == 'gains' else 'azimuth'
    results = [getattr(gains_on_azimuth, attribute_name) for gains_on_azimuth in receiver_gains_per_azimuth]
    assert results == expected_results, f'{results} != {expected_results}'
