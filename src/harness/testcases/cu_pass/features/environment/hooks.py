from dataclasses import dataclass

from behave import runner

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator import \
    GainAtAzimuth, InterferenceComponents


@dataclass
class ContextSas(runner.Context):
    with_integration: bool


def total_interference_before_scenario(context: ContextSas):
    context.interference_components = InterferenceComponents(distance_in_kilometers=0,
                                                             eirp=0,
                                                             frequency_dependent_rejection=0,
                                                             gain_receiver=[GainAtAzimuth(azimuth=0, gain=0)],
                                                             loss_building=0,
                                                             loss_clutter=0,
                                                             loss_propagation=0,
                                                             loss_receiver=0,
                                                             loss_transmitter=0)

