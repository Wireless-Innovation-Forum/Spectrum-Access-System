from abc import ABC, abstractmethod
from typing import Dict, List

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    GainAtAzimuth
from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.utilities import get_bearing_between_two_points, get_dpa_center, Point
from reference_models.dpa.move_list import findAzimuthRange


class AntennaGainCalculator(ABC):
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> Dict[float, GainAtAzimuth]:
        return {
            azimuth: GainAtAzimuth(
                azimuth=azimuth,
                gain=self._calculate_gain_in_direction(azimuth=azimuth)
            )
            for azimuth in self._azimuths
        }

    @abstractmethod
    def _calculate_gain_in_direction(self, azimuth: float) -> float:
        raise NotImplementedError

    @property
    def _azimuths(self) -> List[float]:
        return findAzimuthRange(self._dpa.azimuth_range[0], self._dpa.azimuth_range[1], self._dpa.beamwidth)

    @property
    def _bearing(self) -> float:
        return get_bearing_between_two_points(point1=self._dpa_center, point2=self._cbsd.location)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
