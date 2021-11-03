from dataclasses import dataclass

import parse
from behave import *
from behave import runner

from dpa_calculator.utils import Point, move_distance
from reference_models.dpa.dpa_mgr import BuildDpa, Dpa
from reference_models.ppa.ppa import MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
from reference_models.propagation.wf_itm import CalcItmPropagationLoss

CBSD_A_INDICATOR = 'CBSD_A'
CBSD_B_INDICATOR = 'CBSD_B'

use_step_matcher("parse")


class Cbsd:
    transmit_power: int
    location: Point = None


class CbsdA(Cbsd):
    transmit_power = 30


class CbsdB(Cbsd):
    transmit_power = 47


@dataclass
class ContextDpaParameters(runner.Context):
    cbsd: Cbsd
    dpa: Dpa


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


# @given("{cbsd:Cbsd}_1 is {distance:d} kilometeres away from Hat Creek")
# def step_impl(context: ContextDpaParameters, cbsd: Cbsd, distance: int):
#     """
#     :type context: behave.runner.Context
#     :type cbsd: str
#     :type distance: str
#     """
#     context.cbsd = cbsd
#     context.distance_in_kilometers = distance
#
#
# @then("R_C_DPA_A_HatCreek is 50 kilometers")
# def step_impl(context: ContextDpaParameters):
#     """
#     solve for distance: transmit_power - loss <= -247
#
#     :type context: behave.runner.Context
#     """
#     CalcItmPropagationLoss
#     point_to_point()
#     raise NotImplementedError(u'STEP: Then R_C_DPA_A_HatCreek is 50 kilometers')


@given("{cbsd:Cbsd}_1 is {kilometers:f} kilometers away from {dpa:Dpa}")
def step_impl(context: ContextDpaParameters, cbsd: Cbsd, kilometers: float, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    dpa_origin = Point.from_shapely(point_shapely=dpa.geometry.centroid)
    distant_location = move_distance(bearing=0, kilometers=kilometers, origin=dpa_origin)
    cbsd.location = distant_location

    context.cbsd = cbsd
    context.dpa = dpa


@then("the propagation loss is high enough to make the interference negligible")
def step_impl(context: ContextDpaParameters):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsd_location = context.cbsd.location
    dpa_location = Point.from_shapely(point_shapely=context.dpa.geometry.centroid)
    loss = CalcItmPropagationLoss(lat_cbsd=cbsd_location.latitude, lon_cbsd=cbsd_location.longitude, height_cbsd=context.dpa.radar_height,
                                  lat_rx=dpa_location.latitude, lon_rx=dpa_location.longitude, height_rx=context.dpa.radar_height)
    assert loss == MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
