from dataclasses import dataclass

import parse
from behave import *

from testcases.cu_pass.dpa_calculator.features.environment.global_parsers import NUMBER_REGEX, parse_number

RANGE_DELIMITER = '-'
RANGE_REGEX = rf'{NUMBER_REGEX}({RANGE_DELIMITER}{NUMBER_REGEX})?'


@dataclass
class NumberRange:
    high: float
    low: float


@parse.with_pattern(RANGE_REGEX)
def parse_number_range(text: str) -> NumberRange:
    endpoints = text.split(RANGE_DELIMITER)
    high_text = endpoints[1 if len(endpoints) > 1 else 0]
    low_text = endpoints[0]
    return NumberRange(
        high=parse_number(text=high_text),
        low=parse_number(text=low_text)
    )


register_type(NumberRange=parse_number_range)
