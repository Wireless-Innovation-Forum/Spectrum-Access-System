from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher('parse')


@then('EIRPs in the interference components should match those in the cbsds')
def step_impl(context: ContextCbsdInterference):
    eirps_cbsds = [cbsd.eirp for cbsd in context.cbsds]
    eirps_interference = [components.eirp for components in context.interference_components]
    assert eirps_cbsds == eirps_interference


@then('all {antenna_end} insertion losses should be {expected_power:Integer} dB')
def step_impl(context: ContextCbsdInterference, antenna_end: str, expected_power: int):
    attribute_name = 'loss_transmitter' if antenna_end == 'transmitter' else 'loss_receiver'
    assert all(getattr(components, attribute_name) == expected_power for components in context.interference_components)
