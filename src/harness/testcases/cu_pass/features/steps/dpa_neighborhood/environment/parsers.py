import parse
from behave import *

from dpa_calculator.cbsd import CBSD_A_INDICATOR, CBSD_B_INDICATOR, Cbsd
from reference_models.dpa.dpa_mgr import BuildDpa


# @dataclass
# class CbsdB(Cbsd):
#     transmit_power = 47


@parse.with_pattern(f'({CBSD_A_INDICATOR}|{CBSD_B_INDICATOR})')
def parse_cbsd(text: str) -> Cbsd:
    pass
    # if text == CBSD_A_INDICATOR:
    #     return Ap()
    # else:
    #     return CbsdB()


@parse.with_pattern('.*')
def parse_dpa(text: str):
    return BuildDpa(dpa_name=text.upper())


register_type(Cbsd=parse_cbsd)
register_type(Dpa=parse_dpa)
