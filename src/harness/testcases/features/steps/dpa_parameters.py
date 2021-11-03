from dataclasses import dataclass

import parse
from behave import *
from behave import runner

from reference_models.propagation.itm.itm import point_to_point

CBSD_A_INDICATOR = 'CBSD_A'
CBSD_B_INDICATOR = 'CBSD_B'

use_step_matcher("parse")


class Cbsd:
    transmit_power: int


class CbsdA(Cbsd):
    transmit_power = 30


class CbsdB(Cbsd):
    transmit_power = 47


@dataclass
class ContextDpaParameters(runner.Context):
    cbsd: Cbsd
    distance_in_kilometers: int


@parse.with_pattern(f'[{CBSD_A_INDICATOR}{CBSD_B_INDICATOR}]')
def parse_cbsd(text: str) -> Cbsd:
    if text == CBSD_A_INDICATOR:
        return CbsdA()
    else:
        return CbsdB()


register_type(Cbsd=parse_cbsd)


@given("{cbsd:Cbsd}_1 is {distance:d} kilometeres away from Hat Creek")
def step_impl(context: ContextDpaParameters, cbsd: Cbsd, distance: int):
    """
    :type context: behave.runner.Context
    :type cbsd: str
    :type distance: str
    """
    context.cbsd = cbsd
    context.distance_in_kilometers = distance


@then("R_C_DPA_A_HatCreek is 50 kilometers")
def step_impl(context: ContextDpaParameters):
    """
    solve for distance: transmit_power - loss <= -247

    :type context: behave.runner.Context
    """
    point_to_point()
    raise NotImplementedError(u'STEP: Then R_C_DPA_A_HatCreek is 50 kilometers')
