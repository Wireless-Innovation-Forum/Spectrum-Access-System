from contextlib import contextmanager
from typing import ContextManager
from unittest import mock

from behave import fixture, runner, use_fixture

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers import \
    propagation_loss_calculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    GainAtAzimuth, InterferenceComponents
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa


class ContextSas(runner.Context):
    exception: Exception
    exception_expected: bool


def set_context_sas_defaults(context: ContextSas) -> None:
    context.exception = None
    context.exception_expected = False


@contextmanager
def record_exception_if_expected(context: ContextSas) -> ContextManager[None]:
    if context.exception_expected:
        with _record_exception(context=context):
            yield
    else:
        yield


@contextmanager
def _record_exception(context: ContextSas) -> ContextManager[None]:
    try:
        yield
    except Exception as e:
        context.exception = e


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


def setup_monte_carlo_runner(context: ContextSas):
    context.cbsd_deployment_options = CbsdDeploymentOptions()
    context.include_ue_runs = False


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
