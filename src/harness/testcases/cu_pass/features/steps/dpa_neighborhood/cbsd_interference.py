from dataclasses import dataclass
from typing import List

from behave import *

from dpa_calculator.aggregate_interference_monte_carlo_calculator import InterferenceParameters
from dpa_calculator.cbsd.cbsd import Cbsd, InterferenceComponents
from dpa_calculator.constants import REGION_TYPE_RURAL
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import REGION_TYPE_TO_DPA_NAME_MAP

use_step_matcher('parse')


@dataclass
class ContextCbsdInterference(ContextCbsdCreation, InterferenceParameters, ContextDpa):
    interference_components: List[InterferenceComponents]


@when('interference components are calculated for each CBSD')
def step_impl(context: ContextCbsdInterference):
    context.interference_components = [cbsd.calculate_interference(dpa=context.dpa) for cbsd in context.cbsds]


@then('EIRPs in the interference components should match those in the cbsds')
def step_impl(context: ContextCbsdInterference):
    eirps_cbsds = [cbsd.eirp for cbsd in context.cbsds]
    eirps_interference = [components.eirp for components in context.interference_components]
    assert eirps_cbsds == eirps_interference


@then('all {antenna_end} insertion losses should be {expected_power:Integer} dB')
def step_impl(context: ContextCbsdInterference, antenna_end: str, expected_power: int):
    attribute_name = 'loss_transmitter' if antenna_end == 'transmitter' else 'loss_receiver'
    assert all(getattr(components, attribute_name) == expected_power for components in context.interference_components)


@step('a CBSD at a location with larger {larger_loss_model} with height {height_in_kilometers:Integer}')
def step_impl(context: ContextCbsdInterference, larger_loss_model: str, height_in_kilometers: int):
    if context.dpa.name == REGION_TYPE_TO_DPA_NAME_MAP[REGION_TYPE_RURAL]:
        coordinates = Point(latitude=33.19313987787715, longitude=-96.36484196127637)
    else:
        coordinates = Point(latitude=40.19146905688054, longitude=-76.13331647039989)\
            if larger_loss_model == 'ITM' \
            else Point(latitude=39.78257723575214, longitude=-75.81383219225971)
    context.cbsds = [Cbsd(height=height_in_kilometers, location=coordinates)]


@then('the propagation loss should be {expected_loss:Number}')
def step_impl(context: ContextCbsdInterference, expected_loss: float):
    actual_loss = context.interference_components[0].loss_propagation
    assert actual_loss == expected_loss, f'{actual_loss} != {expected_loss}'
