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
RANGE_REGEX = rf'({NUMBER_REGEX})({RANGE_DELIMITER}({NUMBER_REGEX}))?'


@dataclass
class NumberRange:
    high: float
    low: float


@parse.with_pattern(RANGE_REGEX)
def parse_number_range(text: str) -> NumberRange:
    range_text = re.compile(RANGE_REGEX).search(text)[0]
    low_text = re.compile(NUMBER_REGEX).search(range_text)[0]
    high_text = range_text.replace(f'{low_text}-', '')
    return NumberRange(
        high=parse_number(text=high_text),
        low=parse_number(text=low_text)
    )
