import re
from typing import List

import parse
from behave import register_type

from cu_pass.dpa_calculator.helpers.list_distributor import FractionalDistribution
from testcases.cu_pass.features.environment.global_parsers import NUMBER_REGEX, parse_number
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.range_parser import parse_number_range, \
    RANGE_REGEX

PERCENTAGE_DELIMITER = ':'
DISTRIBUTION_REGEX = rf'({NUMBER_REGEX}%{PERCENTAGE_DELIMITER} {RANGE_REGEX},? ?)'
DISTRIBUTION_LIST_REGEX = rf'{DISTRIBUTION_REGEX}+'


@parse.with_pattern(DISTRIBUTION_LIST_REGEX)
def parse_fractional_distribution(text: str) -> List[FractionalDistribution]:
    distribution_texts = re.compile(DISTRIBUTION_REGEX).findall(text)
    distributions = []
    for distribution_text in distribution_texts:
        percentage_text, height_range_text = distribution_text[0].split(PERCENTAGE_DELIMITER)
        height_range = parse_number_range(text=height_range_text)
        distributions.append(FractionalDistribution(
            range_maximum=height_range.high,
            range_minimum=height_range.low,
            fraction=parse_number(text=percentage_text) / 100
        ))
    return distributions


register_type(FractionalDistribution=parse_fractional_distribution)
