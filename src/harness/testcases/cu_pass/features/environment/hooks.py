from dataclasses import dataclass
from unittest import mock

from behave import fixture, runner, use_fixture

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers import \
    propagation_loss_calculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    GainAtAzimuth, InterferenceComponents
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa


@dataclass
class ContextSas(runner.Context):
    with_integration: bool


@fixture()
def mock_itm(*args):
    with mock.patch.object(propagation_loss_calculator, 'CalcItmPropagationLoss') as itm_loss:
        arbitrary_loss = 0
        itm_loss.return_value.db_loss = arbitrary_loss
        yield


def antenna_gains_before_scenario(context: ContextSas):
    assign_arbitrary_dpa(context=context)


def interference_contribution_eirps_before_scenario(context: ContextSas):
    use_fixture(mock_itm, context=context)


def neighborhood_calculation_before_scenario(context: ContextSas):
    context.monte_carlo_runner = AggregateInterferenceMonteCarloCalculator


def logging_is_captured_before_scenario(context: ContextSas):
    neighborhood_calculation_before_scenario(context=context)


def total_interference_before_scenario(context: ContextSas):
    context.interference_components = InterferenceComponents(distance_in_kilometers=0,
                                                             eirp=0,
                                                             frequency_dependent_rejection=0,
                                                             gain_receiver={0: GainAtAzimuth(azimuth=0, gain=0)},
                                                             loss_building=0,
                                                             loss_clutter=0,
                                                             loss_propagation=0,
                                                             loss_receiver=0,
                                                             loss_transmitter=0)


def transmitter_insertion_losses_before_scenario(context: ContextSas):
    use_fixture(mock_itm, context=context)
