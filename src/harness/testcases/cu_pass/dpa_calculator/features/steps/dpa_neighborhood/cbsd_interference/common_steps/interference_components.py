from typing import Optional

import parse
from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    ReceiveAntennaGainTypes
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsds_generator import CbsdsWithBearings
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    cbsd_creation_step
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.neighborhood_calculation import set_number_of_ues

use_step_matcher('cfparse')


RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM = 'uniform'
RECEIVE_ANTENNA_GAIN_TYPE_STANDARD = 'standard'


@parse.with_pattern(f' with ({RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM}|{RECEIVE_ANTENNA_GAIN_TYPE_STANDARD}) receive antenna gain')
def parse_receive_antenna_gain_calculator_type(text: str) -> ReceiveAntennaGainTypes:
    if RECEIVE_ANTENNA_GAIN_TYPE_STANDARD in text:
        return ReceiveAntennaGainTypes.standard
    if RECEIVE_ANTENNA_GAIN_TYPE_UNIFORM in text:
        return ReceiveAntennaGainTypes.pattern


register_type(ReceiveAntennaGainType=parse_receive_antenna_gain_calculator_type)


@step('interference components are calculated for each {cbsd_type:Any?}CBSD{receive_antenna_gain_type:ReceiveAntennaGainType?}')
def step_impl(context: ContextCbsdInterference, cbsd_type: Optional[str], receive_antenna_gain_type: ReceiveAntennaGainTypes):
    def set_argument_defaults():
        nonlocal receive_antenna_gain_type
        nonlocal cbsd_type
        if receive_antenna_gain_type is None:
            receive_antenna_gain_type = ReceiveAntennaGainTypes.pattern
        cbsd_type = cbsd_type or ''

    def set_context_defaults():
        if not hasattr(context, 'dpa'):
            assign_arbitrary_dpa(context=context)
        if not hasattr(context, 'cbsds'):
            is_user_equipment = cbsd_type == CbsdTypes.UE.value
            small_number_of_cbsds_for_speed_purposes = 1 if is_user_equipment else 5
            context.cbsd_deployment_options = CbsdDeploymentOptions()
            for cbsd_category in CbsdCategories:
                set_number_of_ues(context=context, number_of_ues=small_number_of_cbsds_for_speed_purposes, cbsd_category=cbsd_category)
            context.cbsd_deployment_options.population_override = 10000
            cbsd_creation_step(context=context, is_user_equipment=cbsd_type)

    def perform_interference():
        context.interference_components = AggregateInterferenceCalculatorNtia(
            cbsds_with_bearings=CbsdsWithBearings(cbsds=context.cbsds, bearings=context.bearings),
            dpa=context.dpa,
            receive_antenna_gain_calculator_type=receive_antenna_gain_type).interference_components

    set_argument_defaults()
    set_context_defaults()
    perform_interference()
