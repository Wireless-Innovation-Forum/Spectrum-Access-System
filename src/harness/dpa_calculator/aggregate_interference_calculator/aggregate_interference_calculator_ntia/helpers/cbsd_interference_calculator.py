import random
from dataclasses import dataclass
from typing import List

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsd.cbsd_interference_calculator.helpers.propagation_loss_calculator import \
    PropagationLossCalculator
from dpa_calculator.utilities import get_bearing_between_two_points, get_distance_between_two_points, get_dpa_center, \
    Point, region_is_rural
from reference_models.antenna.antenna import GetRadarNormalizedAntennaGains, GetStandardAntennaGains
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import findAzimuthRange

CLUTTER_LOSS_MAXIMUM = 15
CLUTTER_LOSS_MINIMUM = 0
INSERTION_LOSSES_IN_DB = 2


@dataclass
class GainAtAzimuth:
    azimuth: float
    gain: float


@dataclass
class InterferenceComponents:
    distance_in_kilometers: float
    eirp: float
    frequency_dependent_rejection: float
    gain_receiver: List[GainAtAzimuth]
    loss_building: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float

    def total_interference(self, azimuth: float) -> float:
        receiver_gain = next(gain_at_azimuth.gain for gain_at_azimuth in self.gain_receiver if gain_at_azimuth.azimuth == azimuth)
        return self.eirp \
               + receiver_gain \
               - self.loss_transmitter \
               - self.loss_receiver \
               - self.loss_propagation \
               - self.loss_clutter \
               - self.loss_building \
               - self.frequency_dependent_rejection


class CbsdInterferenceCalculator:
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> InterferenceComponents:
        return InterferenceComponents(
            distance_in_kilometers=get_distance_between_two_points(point1=self._dpa_center, point2=self._cbsd.location),
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
    def _gain_receiver(self) -> List[GainAtAzimuth]:
        bearing = get_bearing_between_two_points(point1=self._dpa_center, point2=self._cbsd.location)
        azimuths = findAzimuthRange(self._dpa.azimuth_range[0], self._dpa.azimuth_range[1], self._dpa.beamwidth)
        return [GainAtAzimuth(
            azimuth=azimuth,
            gain=GetStandardAntennaGains(hor_dirs=bearing, ant_azimuth=azimuth, ant_beamwidth=self._dpa.beamwidth)
        ) for azimuth in azimuths]

    @property
    def _is_rural(self) -> bool:
        return region_is_rural(coordinates=self._dpa_center)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
