from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional

from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.configuration.configuration_manager import \
    ConfigurationManager
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation

use_step_matcher("cfparse")


@dataclass
class ContextTransmissionPower(ContextCbsdCreation):
    pass


@given("a {is_indoor:IsIndoor} category {cbsd_category:CbsdCategory} {cbsd_type:CbsdType} eirp distribution of {distributions:FractionalDistribution}")
def step_impl(context: ContextTransmissionPower, is_indoor: bool, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes, distributions: List[FractionalDistribution]):
    configuration = ConfigurationManager().get_configuration()
    configuration.eirp_distribution[cbsd_type][cbsd_category] = defaultdict(lambda: {is_indoor: distributions[0]})


@then("the {is_indoor:IsIndoor?}antenna maximum EIRPs should be {expected_powers:FractionalDistribution} dBm")
def step_impl(context: ContextTransmissionPower, is_indoor: Optional[bool], expected_powers: List[FractionalDistribution]):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsds = context.cbsds if is_indoor is None else (cbsd for cbsd in context.cbsds if cbsd.is_indoor == is_indoor)
    max_eirps = [cbsd.eirp_maximum for cbsd in cbsds]
    for expected_power in expected_powers:
        expected_power.assert_data_matches_distribution(data=max_eirps)
