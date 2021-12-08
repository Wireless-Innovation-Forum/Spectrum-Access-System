import parse
from behave import *

from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.dpa.builder import get_dpa


@parse.with_pattern('.*')
def parse_dpa(text: str) -> Dpa:
    return get_dpa(dpa_name=text)


register_type(Dpa=parse_dpa)
