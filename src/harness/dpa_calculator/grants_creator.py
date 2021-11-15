from typing import List

from cached_property import cached_property

from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from testcases.cu_pass.features.steps.dpa_parameters.environment.parsers import CBSD_A_INDICATOR, Cbsd, get_cbsd_ap

PERCENTAGE_OF_INDOOR_APS_RURAL = 0.99


class GrantsCreator:
    def __init__(self, dpa: Dpa, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa = dpa
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> List[CbsdGrantInfo]:
        return [ap.to_grant() for ap in self._all_cbsds]

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=True, location=location)
                for location in self._indoor_cbsd_locations]

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[:self._number_of_indoor_cbsds]

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=False, location=location)
                for location in self._outdoot_cbsd_locations]

    @property
    def _outdoot_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[self._number_of_indoor_cbsds:]

    @cached_property
    def _distributed_cbsds(self) -> List[Point]:
        return PointDistributor(distribution_area=self._dpa_zone).distribute_points(number_of_points=self._number_of_cbsds)

    @property
    def _number_of_indoor_cbsds(self):
        return int(self._number_of_cbsds * PERCENTAGE_OF_INDOOR_APS_RURAL)
