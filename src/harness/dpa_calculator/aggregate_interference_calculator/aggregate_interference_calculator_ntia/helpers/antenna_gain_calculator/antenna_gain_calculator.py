from abc import ABC, abstractmethod
from typing import Dict, List

import numpy

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    GainAtAzimuth
from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.utilities import get_dpa_center, Point
from reference_models.dpa.move_list import findAzimuthRange


class AntennaGainCalculator(ABC):
    def __init__(self, bearings: List[float], cbsds: List[Cbsd], dpa: Dpa):
        self._bearings = numpy.asarray(bearings)
        self._cbsds = cbsds
        self._dpa = dpa

    def calculate(self) -> List[Dict[float, GainAtAzimuth]]:
        return [self._gains_per_azimuth(cbsd_gains=cbsd_gains) for cbsd_gains in self._gains_per_cbsd]

    def _gains_per_azimuth(self, cbsd_gains: numpy.ndarray) -> Dict[float, GainAtAzimuth]:
        return {
            azimuth: GainAtAzimuth(azimuth=azimuth, gain=cbsd_gains[azimuth_index])
            for azimuth_index, azimuth in enumerate(self._azimuths)
        }

    @property
    def _gains_per_cbsd(self) -> numpy.ndarray:
        gains = numpy.asarray([self._calculate_gains_in_direction(azimuth=azimuth) for azimuth in self._azimuths])
        return gains.transpose()

    @abstractmethod
    def _calculate_gains_in_direction(self, azimuth: float) -> numpy.ndarray:
        raise NotImplementedError

    @property
    def _azimuths(self) -> List[float]:
        return findAzimuthRange(self._dpa.azimuth_range[0], self._dpa.azimuth_range[1], self._dpa.beamwidth)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
