import re
from dataclasses import dataclass
from typing import List

import parse
from behave import *

from dpa_calculator.grants_creator.cbsd_height_distributor import HeightDistribution
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.environment.global_parsers import INTEGER_REGEX, parse_integer
from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher("parse")

PERCENTAGE_DELIMITER = ':'
RANGE_DELIMITER = '-'

HEIGHT_DISTRIBUTION_REGEX = rf'({INTEGER_REGEX}%{PERCENTAGE_DELIMITER} {INTEGER_REGEX}({RANGE_DELIMITER}{INTEGER_REGEX})?,? ?)'


@parse.with_pattern(rf'{HEIGHT_DISTRIBUTION_REGEX}+')
def parse_height_distribution(text: str) -> List[HeightDistribution]:
    distributions = re.compile(HEIGHT_DISTRIBUTION_REGEX).findall(text)
    height_distributions = []
    for distribution_text in distributions:
        percentage_text, height_range_text = distribution_text[0].split(PERCENTAGE_DELIMITER)
        height_endpoints = height_range_text.split(RANGE_DELIMITER)
        min_height_text = height_endpoints[0]
        max_height_text = height_endpoints[1 if len(height_endpoints) > 1 else 0]
        height_distributions.append(HeightDistribution(
            maximum_height_in_meters=parse_integer(text=max_height_text),
            minimum_height_in_meters=parse_integer(text=min_height_text),
            fraction_of_cbsds=parse_integer(text=percentage_text) / 100
        ))
    return height_distributions


register_type(HeightDistribution=parse_height_distribution)


@dataclass
class ContextApHeights(ContextGrantCreation):
    pass


@then("the indoor antenna heights should fall in distribution {height_distribution:HeightDistribution}")
def step_impl(context: ContextApHeights, height_distribution: List[HeightDistribution]):
    """
    Args:
        context (behave.runner.Context):
        height_distribution (str):
    """
    indoor_grants = get_indoor_grants(grants=context.grants)
    number_of_indoor_grants = len(indoor_grants)
    for distribution in height_distribution:
        grants_in_range = [grant for grant in indoor_grants if distribution.minimum_height_in_meters <= grant.height_agl <= distribution.maximum_height_in_meters]
        number_of_grants_in_range = len(grants_in_range)
        percentage_in_range = number_of_grants_in_range / number_of_indoor_grants
        assert percentage_in_range == distribution.fraction_of_cbsds, \
            f'Range: {distribution.minimum_height_in_meters}-{distribution.maximum_height_in_meters}, Percentage: {percentage_in_range} != {distribution.fraction_of_cbsds}'


@step("indoor antenna heights should be in 0.5 meter increments")
def step_impl(context: ContextApHeights):
    """
    Args:
        context (behave.runner.Context):
    """
    indoor_grants = get_indoor_grants(grants=context.grants)
    assert all((grant.height_agl * 2) % 1 == 0 for grant in indoor_grants)


@step("outdoor antenna heights should be {expected_height:Integer} meters")
def step_impl(context: ContextApHeights, expected_height: int):
    """
    Args:
        context (behave.runner.Context):
    """
    outdoor_grants = [grant for grant in context.grants if not grant.indoor_deployment]
    assert all(grant.height_agl == expected_height for grant in outdoor_grants)


def get_indoor_grants(grants: List[CbsdGrantInfo]) -> List[CbsdGrantInfo]:
    return [grant for grant in grants if grant.indoor_deployment]
