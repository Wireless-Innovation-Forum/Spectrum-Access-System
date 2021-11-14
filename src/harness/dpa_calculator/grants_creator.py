from typing import List, Tuple

from cached_property import cached_property

from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import HIGH_FREQ_COCH, LOW_FREQ_COCH
from testcases.cu_pass.features.steps.dpa_parameters.environment.parsers import CBSD_A_INDICATOR, Cbsd, get_cbsd_ap

COCHANNEL_BANDWIDTH = 10
PERCENTAGE_OF_INDOOR_APS_RURAL = 0.99
HERTZ_IN_MEGAHERTZ = 1e6


class GrantsCreator:
    def __init__(self, dpa: Dpa, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa = dpa
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self):
        return [ap.to_grant(low_frequency=self._low_inband_frequency, high_frequency=self._high_inband_frequency)
                for ap in self._all_cbsds]

    @property
    def _high_inband_frequency(self):
        return self._low_inband_frequency + COCHANNEL_BANDWIDTH * HERTZ_IN_MEGAHERTZ

    @property
    def _low_inband_frequency(self) -> float:
        return self._first_inband_channel[0] * HERTZ_IN_MEGAHERTZ

    @property
    def _first_inband_channel(self) -> Tuple[float, float]:
        return next(channel for channel in self._dpa._channels if
                    channel[0] * 1e6 >= LOW_FREQ_COCH and channel[1] * 1e6 <= HIGH_FREQ_COCH)

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=False, location=location)
                for location in self._outdoot_cbsd_locations]

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=True, location=location) for location in
                (self._indoor_cbsd_locations)]

    @property
    def _outdoot_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[self._number_of_indoor_cbsds:]

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[:self._number_of_indoor_cbsds]

    @cached_property
    def _distributed_cbsds(self) -> List[Point]:
        return PointDistributor(distribution_area=self._dpa_zone).distribute_points(number_of_points=self._number_of_cbsds)

    @property
    def _number_of_indoor_cbsds(self):
        return int(self._number_of_cbsds * PERCENTAGE_OF_INDOOR_APS_RURAL)
