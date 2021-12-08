from dataclasses import dataclass, replace

from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    GainAtAzimuth, InterferenceComponents
from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher("parse")


@dataclass
class ContextTotalCbsdInterference(ContextSas):
    interference_components: InterferenceComponents


@given("an EIRP of {eirp:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, eirp: float):
    """
    Args:
        context (behave.runner.Context):
        eirp (str):
    """
    context.interference_components = replace(context.interference_components, eirp=eirp)


@step("a receive antenna gain of {receive_antenna_gain:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, receive_antenna_gain: float):
    """
    Args:
        context (behave.runner.Context):
        receive_antenna_gain (str):
    """
    context.interference_components = replace(context.interference_components, gain_receiver=[GainAtAzimuth(azimuth=0, gain=receive_antenna_gain)])


@step("a transmitter insertion loss of {insertion_loss:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, insertion_loss: float):
    """
    Args:
        context (behave.runner.Context):
        insertion_loss (str):
    """
    context.interference_components = replace(context.interference_components, loss_transmitter=insertion_loss)


@step("a receiver insertion loss of {insertion_loss:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, insertion_loss: float):
    """
    Args:
        context (behave.runner.Context):
        insertion_loss (str):
    """
    context.interference_components = replace(context.interference_components, loss_receiver=insertion_loss)


@step("a propagation loss of {propagation_loss:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, propagation_loss: float):
    """
    Args:
        context (behave.runner.Context):
        propagation_loss (str):
    """
    context.interference_components = replace(context.interference_components, loss_propagation=propagation_loss)


@step("a clutter loss of {clutter_loss:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, clutter_loss: float):
    """
    Args:
        context (behave.runner.Context):
        clutter_loss (str):
    """
    context.interference_components = replace(context.interference_components, loss_clutter=clutter_loss)


@step("a building loss of {building_loss:Number} dB")
def step_impl(context: ContextTotalCbsdInterference, building_loss: float):
    """
    Args:
        context (behave.runner.Context):
        building_loss (str):
    """
    context.interference_components = replace(context.interference_components, loss_building=building_loss)


@then("the total interference should be {expected_interference:Number}")
def step_impl(context: ContextTotalCbsdInterference, expected_interference: float):
    """
    Args:
        context (behave.runner.Context):
        expected_interference (str):
    """
    interference = context.interference_components.total_interference(azimuth=0)
    assert interference == expected_interference, f'{interference} != {expected_interference}'
