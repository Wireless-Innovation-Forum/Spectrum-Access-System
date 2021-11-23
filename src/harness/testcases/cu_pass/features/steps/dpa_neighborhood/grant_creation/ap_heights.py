import re
from dataclasses import dataclass
from typing import List

import parse
from behave import *

from testcases.cu_pass.features.environment.global_parsers import INTEGER_REGEX, parse_integer
from testcases.cu_pass.features.steps.dpa_neighborhood.grant_creation.common_steps.grant_creation import \
    ContextGrantCreation

use_step_matcher("parse")

PERCENTAGE_DELIMITER = ':'
RANGE_DELIMITER = '-'

HEIGHT_DISTRIBUTION_REGEX = rf'({INTEGER_REGEX}%{PERCENTAGE_DELIMITER} {INTEGER_REGEX}({RANGE_DELIMITER}{INTEGER_REGEX})?,? ?)'


@dataclass
class HeightDistribution:
    maximum_height_in_meters: int
    minimum_height_in_meters: int
    percentage_of_cbsds: float


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
            percentage_of_cbsds=parse_integer(text=percentage_text) / 100
        ))
    return height_distributions


register_type(HeightDistribution=parse_height_distribution)


@dataclass
class ContextApHeights(ContextGrantCreation):
    pass


@then("the antenna heights should fall in distribution {height_distribution:HeightDistribution}")
def step_impl(context: ContextApHeights, height_distribution: List[HeightDistribution]):
    """
    Args:
        context (behave.runner.Context):
        height_distribution (str):
    """
    total_number_of_grants = len(context.grants)
    for distribution in height_distribution:
        number_in_range = sum(1 for grant in context.grants if distribution.minimum_height_in_meters <= grant.height_agl <= distribution.maximum_height_in_meters)
        percentage_in_range = number_in_range / total_number_of_grants
        assert percentage_in_range == distribution.percentage_of_cbsds, f'Range: {distribution.minimum_height_in_meters}-{distribution.maximum_height_in_meters}, Percentage: {percentage_in_range} != {distribution.percentage_of_cbsds}'
