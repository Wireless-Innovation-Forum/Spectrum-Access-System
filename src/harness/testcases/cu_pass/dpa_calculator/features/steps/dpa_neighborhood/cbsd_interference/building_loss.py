from typing import List

import parse
from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.building_loss_distributor import \
    BuildingLossDistribution, fractional_distribution_to_building_loss_distribution
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.support.fractional_distribution_parser import \
    DISTRIBUTION_REGEX_UNIFORM, parse_fractional_distribution

use_step_matcher('parse')


@parse.with_pattern(rf'{DISTRIBUTION_REGEX_UNIFORM}+')
def parse_height_distribution(text: str) -> List[BuildingLossDistribution]:
    distributions = parse_fractional_distribution(text=text)
    return [fractional_distribution_to_building_loss_distribution(distribution=distribution) for distribution in distributions]


register_type(BuildingLossDistribution=parse_height_distribution)


@then("the building attenuation losses follow the distribution {distributions:BuildingLossDistribution}")
def step_impl(context: ContextCbsdInterference, distributions: List[BuildingLossDistribution]):
    """
    Args:
        context (behave.runner.Context):
    """
    for distribution in distributions:
        loss_matches = [interference_component for interference_component in context.interference_components
                        if distribution.loss_in_db == interference_component.loss_building]
        fraction_in_range = len(loss_matches) / len(context.cbsds)
        assert fraction_in_range == distribution.fraction, \
            f'{distribution.loss_in_db} dB: {fraction_in_range} != {distribution.fraction}'
