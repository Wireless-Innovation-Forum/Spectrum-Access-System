from dataclasses import dataclass
from typing import List

import parse
from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import \
    fractional_distribution_to_height_distribution, HeightDistribution
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.support.fractional_distribution_parser import \
    DISTRIBUTION_REGEX_UNIFORM, parse_fractional_distribution

use_step_matcher("parse")


@parse.with_pattern(rf'{DISTRIBUTION_REGEX_UNIFORM}+')
def parse_height_distribution(text: str) -> List[HeightDistribution]:
    distributions = parse_fractional_distribution(text=text)
    return [fractional_distribution_to_height_distribution(distribution=distribution) for distribution in distributions]


register_type(HeightDistribution=parse_height_distribution)


@dataclass
class ContextApHeights(ContextCbsdCreation):
    pass


@then("the {is_indoor:IsIndoor} antenna heights should fall in distribution {height_distribution:HeightDistribution}")
def step_impl(context: ContextApHeights, is_indoor: bool, height_distribution: List[HeightDistribution]):
    """
    Args:
        context (behave.runner.Context):
        is_indoor (str):
        height_distribution (str):
    """
    cbsds_on_correct_side = [cbsd for cbsd in context.cbsds if cbsd.is_indoor == is_indoor]
    for distribution in height_distribution:
        cbsd_heights = [cbsd.height_in_meters for cbsd in cbsds_on_correct_side]
        distribution.to_fractional_distribution().assert_data_matches_distribution(data=cbsd_heights, leeway_fraction=0.01)


@step("antenna heights should be in 0.5 meter increments")
def step_impl(context: ContextApHeights):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_grants = context.cbsds
    assert all((cbsd.height_in_meters * 2) % 1 == 0 for cbsd in indoor_grants)


def get_indoor_grants(cbsds: List[Cbsd]) -> List[Cbsd]:
    return [cbsd for cbsd in cbsds if cbsd.is_indoor]
