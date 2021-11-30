from dataclasses import dataclass
from typing import List

import parse
from behave import *

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import \
    fractional_distribution_to_height_distribution, HeightDistribution
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_fractional_distribution import \
    DISTRIBUTION_REGEX, parse_fractional_distribution

use_step_matcher("parse")


@parse.with_pattern(rf'{DISTRIBUTION_REGEX}+')
def parse_height_distribution(text: str) -> List[HeightDistribution]:
    distributions = parse_fractional_distribution(text=text)
    return [fractional_distribution_to_height_distribution(distribution=distribution) for distribution in distributions]


register_type(HeightDistribution=parse_height_distribution)


@dataclass
class ContextApHeights(ContextCbsdCreation):
    pass


@then("the indoor antenna heights should fall in distribution {height_distribution:HeightDistribution}")
def step_impl(context: ContextApHeights, height_distribution: List[HeightDistribution]):
    """
    Args:
        context (behave.runner.Context):
        height_distribution (str):
    """
    indoor_grants = get_indoor_grants(cbsds=context.cbsds)
    number_of_indoor_grants = len(indoor_grants)
    for distribution in height_distribution:
        grants_in_range = [cbsd for cbsd in indoor_grants if distribution.minimum_height_in_meters <= cbsd.height <= distribution.maximum_height_in_meters]
        number_of_grants_in_range = len(grants_in_range)
        fraction_in_range = number_of_grants_in_range / number_of_indoor_grants
        assert round(fraction_in_range, 2) == distribution.fraction_of_cbsds, \
            f'Range: {distribution.minimum_height_in_meters}-{distribution.maximum_height_in_meters}, Percentage: {fraction_in_range} != {distribution.fraction_of_cbsds}'


@step("indoor antenna heights should be in 0.5 meter increments")
def step_impl(context: ContextApHeights):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_grants = get_indoor_grants(cbsds=context.cbsds)
    assert all((cbsd.height * 2) % 1 == 0 for cbsd in indoor_grants)


@step("outdoor antenna heights should be {expected_height:Number} meters")
def step_impl(context: ContextApHeights, expected_height: float):
    """
    Args:
        context (behave.runner.Context):
    """
    outdoor_grants = [cbsd for cbsd in context.cbsds if not cbsd.is_indoor]
    assert all(grant.height == expected_height for grant in outdoor_grants)


def get_indoor_grants(cbsds: List[Cbsd]) -> List[Cbsd]:
    return [cbsd for cbsd in cbsds if cbsd.is_indoor]
