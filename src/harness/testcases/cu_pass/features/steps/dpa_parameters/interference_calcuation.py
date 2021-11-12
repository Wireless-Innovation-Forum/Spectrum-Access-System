from dataclasses import dataclass

from behave import *
from behave import runner

from dpa_calculator.utils import Point, move_distance
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.ppa.ppa import MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
from reference_models.propagation.wf_itm import CalcItmPropagationLoss
from testcases.cu_pass.features.steps.dpa_parameters.environment.parsers import Cbsd


@dataclass
class ContextPropagationLoss(runner.Context):
    cbsd: Cbsd
    dpa: Dpa


class InterferenceCalculator:
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def get_itm_interference(self) -> float:
        calculated_loss = CalcItmPropagationLoss(lat_cbsd=self._cbsd_location.latitude,
                                                 lon_cbsd=self._cbsd_location.longitude,
                                                 height_cbsd=self._dpa.radar_height,
                                                 lat_rx=self._dpa_location.latitude,
                                                 lon_rx=self._dpa_location.longitude,
                                                 height_rx=self._dpa.radar_height)
        return calculated_loss.db_loss

    @property
    def _cbsd_location(self) -> Point:
        return self._cbsd.location

    @property
    def _dpa_location(self) -> Point:
        return Point.from_shapely(point_shapely=self._dpa.geometry.centroid)


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


@then("the interference at the receiver is 5")
def step_impl(context: ContextPropagationLoss):
    """
    Args:
        context (behave.runner.Context):
    """
    loss = InterferenceCalculator(cbsd=context.cbsd, dpa=context.dpa)
    assert loss == MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
