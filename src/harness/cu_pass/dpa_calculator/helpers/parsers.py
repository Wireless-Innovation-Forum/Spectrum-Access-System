import re
from dataclasses import dataclass

import parse

INTEGER_REGEX = r'-?[0-9]+(,[0-9]{3})*'
NUMBER_REGEX = rf'({INTEGER_REGEX}(\.[0-9]+)?|infinity|-infinity)'


@parse.with_pattern(NUMBER_REGEX)
def parse_number(text: str) -> float:
    number_text = re.compile(NUMBER_REGEX).search(text)
    return float(number_text[0].replace(',', ''))


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