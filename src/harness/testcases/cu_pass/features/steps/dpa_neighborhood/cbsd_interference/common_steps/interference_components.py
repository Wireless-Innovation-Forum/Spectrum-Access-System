from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher('parse')


@when('interference components are calculated for each CBSD')
def step_impl(context: ContextCbsdInterference):
    if not hasattr(context, 'dpa'):
        assign_arbitrary_dpa(context=context)
    if not hasattr(context, 'cbsds'):
        small_number_of_cbsds_for_speed_purposes = 5
        context.execute_steps(f'When {small_number_of_cbsds_for_speed_purposes} CBSDs for the Monte Carlo simulation are created')
    context.interference_components = AggregateInterferenceCalculatorNtia(cbsds=context.cbsds, dpa=context.dpa).interference_information
