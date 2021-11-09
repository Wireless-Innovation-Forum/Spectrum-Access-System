import parse
from behave import *

from dpa_calculator.utils import Point
from reference_models.dpa.dpa_mgr import BuildDpa

CBSD_A_INDICATOR = 'CBSD_A'
CBSD_B_INDICATOR = 'CBSD_B'


class Cbsd:
    transmit_power: int
    location: Point = None


class CbsdA(Cbsd):
    transmit_power = 30


class CbsdB(Cbsd):
    transmit_power = 47


@parse.with_pattern(f'({CBSD_A_INDICATOR}|{CBSD_B_INDICATOR})')
def parse_cbsd(text: str) -> Cbsd:
    if text == CBSD_A_INDICATOR:
        return CbsdA()
    else:
        return CbsdB()


@parse.with_pattern('.*')
def parse_dpa(text: str):
    return BuildDpa(dpa_name=text.upper())


register_type(Cbsd=parse_cbsd)
register_type(Dpa=parse_dpa)
