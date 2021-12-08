from typing import Optional, Type

import parse
from behave import *

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator_standard import \
    AntennaGainCalculatorStandard
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator_gain_pattern import \
    AntennaGainCalculatorGainPattern
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher('cfparse')


RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM = 'uniform'
RECEIVE_ANTENNA_GAIN_TYPE_STANDARD = 'standard'


@parse.with_pattern(f' with ({RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM}|{RECEIVE_ANTENNA_GAIN_TYPE_STANDARD}) receive antenna gain')
def parse_receive_antenna_gain_calculator_type(text: str) -> Type[AntennaGainCalculator]:
    if RECEIVE_ANTENNA_GAIN_TYPE_STANDARD in text:
        return AntennaGainCalculatorStandard
    if RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM in text:
        return AntennaGainCalculatorGainPattern


register_type(ReceiveAntennaGainType=parse_receive_antenna_gain_calculator_type)


@step('interference components are calculated for each {cbsd_type:Any?}CBSD{receive_antenna_gain_type:ReceiveAntennaGainType?}')
def step_impl(context: ContextCbsdInterference, cbsd_type: Optional[str], receive_antenna_gain_type: Type[AntennaGainCalculator]):
    def set_argument_defaults():
        nonlocal receive_antenna_gain_type
        nonlocal cbsd_type
        if receive_antenna_gain_type is None:
            receive_antenna_gain_type = AntennaGainCalculatorGainPattern
        cbsd_type = cbsd_type or ''

    def set_context_defaults():
        if not hasattr(context, 'dpa'):
            assign_arbitrary_dpa(context=context)
        if not hasattr(context, 'cbsds'):
            small_number_of_cbsds_for_speed_purposes = 5
            context.execute_steps(f'When {small_number_of_cbsds_for_speed_purposes} {cbsd_type.strip()} CBSDs for the Monte Carlo simulation are created')

    def perform_interference():
        context.interference_components = AggregateInterferenceCalculatorNtia(
            cbsds=context.cbsds,
            dpa=context.dpa,
            receive_antenna_gain_calculator_class=receive_antenna_gain_type).interference_information

    set_argument_defaults()
    set_context_defaults()
    perform_interference()
