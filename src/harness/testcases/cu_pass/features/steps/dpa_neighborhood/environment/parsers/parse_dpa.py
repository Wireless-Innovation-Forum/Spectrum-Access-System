import parse
from behave import *

from cu_pass.dpa_calculator.dpa.builder import get_dpa
from cu_pass.dpa_calculator.dpa.dpa import Dpa


@parse.with_pattern('.*')
def parse_dpa(text: str) -> Dpa:
    return get_dpa(dpa_name=text)


register_type(Dpa=parse_dpa)
