from dataclasses import dataclass

from behave import *
from behave import runner

from dpa_calculator.utils import Point, move_distance
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.ppa.ppa import MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
from reference_models.propagation.wf_itm import CalcItmPropagationLoss
from testcases.features.steps.dpa_parameters.environment import Cbsd


@dataclass
class ContextPropagationLoss(runner.Context):
    cbsd: Cbsd
    dpa: Dpa



@given("{cbsd:Cbsd}_1 is {kilometers:f} kilometers away from {dpa:Dpa}")
def step_impl(context: ContextPropagationLoss, cbsd: Cbsd, kilometers: float, dpa: Dpa):
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
def step_impl(context: ContextPropagationLoss):
    """
    Args:
        context (behave.runner.Context):
    """
    cbsd_location = context.cbsd.location
    dpa_location = Point.from_shapely(point_shapely=context.dpa.geometry.centroid)
    loss = CalcItmPropagationLoss(lat_cbsd=cbsd_location.latitude, lon_cbsd=cbsd_location.longitude, height_cbsd=context.dpa.radar_height,
                                  lat_rx=dpa_location.latitude, lon_rx=dpa_location.longitude, height_rx=context.dpa.radar_height)
    assert loss == MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
