import random
from dataclasses import dataclass
from typing import List

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsd.cbsd_interference_calculator.helpers.propagation_loss_calculator import \
    PropagationLossCalculator
from dpa_calculator.utilities import get_bearing_between_two_points, get_dpa_center, Point, region_is_rural
from reference_models.antenna.antenna import GetRadarNormalizedAntennaGains, GetStandardAntennaGains
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import findAzimuthRange

CLUTTER_LOSS_MAXIMUM = 15
CLUTTER_LOSS_MINIMUM = 0
INSERTION_LOSSES_IN_DB = 2


@dataclass
class GainForAzimuth:
    azimuth: float
    gain: float


@dataclass
class InterferenceComponents:
    eirp: float
    frequency_dependent_rejection: float
    gain_receiver: List[GainForAzimuth]
    loss_building: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float


class CbsdInterferenceCalculator:
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> InterferenceComponents:
        return InterferenceComponents(
            eirp=self._cbsd.eirp,
            frequency_dependent_rejection=0,
            gain_receiver=self._gain_receiver,
            loss_building=0,
            loss_clutter=random.uniform(CLUTTER_LOSS_MINIMUM, CLUTTER_LOSS_MAXIMUM) if self._is_rural else CLUTTER_LOSS_MINIMUM,
            loss_propagation=PropagationLossCalculator(cbsd=self._cbsd, dpa=self._dpa).calculate(),
            loss_receiver=INSERTION_LOSSES_IN_DB,
            loss_transmitter=INSERTION_LOSSES_IN_DB
        )

    @property
    def _gain_receiver(self) -> List[GainForAzimuth]:
        bearing = get_bearing_between_two_points(point1=self._dpa_center, point2=self._cbsd.location)
        azimuths = findAzimuthRange(self._dpa.azimuth_range[0], self._dpa.azimuth_range[1], self._dpa.beamwidth)
        return [GainForAzimuth(
            azimuth=azimuth,
            gain=GetStandardAntennaGains(hor_dirs=bearing, ant_azimuth=azimuth, ant_beamwidth=self._dpa.beamwidth)
        ) for azimuth in azimuths]

    @property
    def _is_rural(self) -> bool:
        return region_is_rural(coordinates=self._dpa_center)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
