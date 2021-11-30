from dataclasses import dataclass
from typing import List

import parse
from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.aggregate_interference_monte_carlo_calculator import InterferenceParameters
from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsd.cbsd_interference_calculator.cbsd_interference_calculator import CbsdInterferenceCalculator, \
    InterferenceComponents
from dpa_calculator.constants import REGION_TYPE_RURAL
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa, \
    REGION_TYPE_TO_DPA_NAME_MAP
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_fractional_distribution import \
    FractionalDistribution
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.range_parser import NumberRange, RANGE_REGEX

use_step_matcher('parse')


@dataclass
class ContextCbsdInterference(ContextCbsdCreation, InterferenceParameters, ContextDpa):
    interference_components: List[InterferenceComponents]


@when('interference components are calculated for each CBSD')
def step_impl(context: ContextCbsdInterference):
    if not hasattr(context, 'dpa'):
        assign_arbitrary_dpa(context=context)
    if not hasattr(context, 'cbsds'):
        small_number_of_cbsds_for_speed_purposes = 5
        context.execute_steps(f'When {small_number_of_cbsds_for_speed_purposes} CBSDs for the Monte Carlo simulation are created')
    context.interference_components = AggregateInterferenceCalculatorNtia(cbsds=context.cbsds, dpa=context.dpa).interference_information


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
    elif larger_loss_model == 'ITM':
        coordinates = Point(latitude=40.19146905688054, longitude=-76.13331647039989)
    else:
        coordinates = Point(latitude=39.78257723575214, longitude=-75.81383219225971)
    context.cbsds = [Cbsd(height=height_in_kilometers, location=coordinates)]


@then('the propagation loss should be {expected_loss:Number}')
def step_impl(context: ContextCbsdInterference, expected_loss: float):
    actual_loss = context.interference_components[0].loss_propagation
    assert actual_loss == expected_loss, f'{actual_loss} != {expected_loss}'


@then("clutter loss distribution is within {expected_clutter_loss_range:NumberRange}")
def step_impl(context: ContextCbsdInterference, expected_clutter_loss_range: NumberRange):
    """
    Args:
        context (behave.runner.Context):
        expected_clutter_loss_range (str):
    """
    def is_out_of_range(loss: float) -> bool:
        return loss < expected_clutter_loss_range.low or loss > expected_clutter_loss_range.high
    out_of_range = [interference_components
                    for interference_components in context.interference_components
                    if is_out_of_range(loss=interference_components.loss_clutter)]
    assert not out_of_range, f'Losses {out_of_range} are out of range {expected_clutter_loss_range.low}-{expected_clutter_loss_range.high}'


@step("not all losses are equal if and only if {expected_clutter_loss_range:NumberRange} is a range")
def step_impl(context: ContextCbsdInterference, expected_clutter_loss_range: NumberRange):
    """
    Args:
        context (behave.runner.Context):
        expected_clutter_loss_range (str):
    """
    is_range = expected_clutter_loss_range.low != expected_clutter_loss_range.high
    unique_losses = set(interference_components.loss_clutter for interference_components in context.interference_components)
    if is_range:
        assert len(unique_losses) > 1
    else:
        assert len(unique_losses) == 1


@then("the building attenuation losses follow the distribution {distributions:FractionalDistribution}")
def step_impl(context: ContextCbsdInterference, distributions: List[FractionalDistribution]):
    """
    Args:
        context (behave.runner.Context):
    """
    for distribution in distributions:
        loss_matches = [interference_component for interference_component in context.interference_components
                        if distribution.range_minimum == interference_component.loss_building]
        fraction_in_range = len(loss_matches) / len(context.cbsds)
        assert fraction_in_range == distribution.fraction, f'{distribution.range_minimum} dB: {fraction_in_range} != {distribution.fraction}'
