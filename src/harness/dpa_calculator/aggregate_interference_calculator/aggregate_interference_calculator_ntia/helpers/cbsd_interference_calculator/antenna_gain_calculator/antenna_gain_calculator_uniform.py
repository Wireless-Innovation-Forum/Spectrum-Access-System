import random

import numpy
from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from dpa_calculator.cbsd.cbsd import Cbsd
from reference_models.antenna.antenna import GetAntennaPatternGains


class AntennaGainCalculatorUniform(AntennaGainCalculator):
    def _calculate_gain_in_direction(self, azimuth: float, cbsd: Cbsd) -> float:
        bearing = self._bearing(cbsd_location=cbsd.location)
        return GetAntennaPatternGains(hor_dirs=bearing,
                                      ant_azimuth=azimuth,
                                      hor_pattern=self._gain_pattern)

    @cached_property
    def _gain_pattern(self) -> numpy.ndarray:
        return numpy.asarray([random.uniform(0, 6) for _ in range(360)])
