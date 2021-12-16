import numpy

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from reference_models.antenna.antenna import GetAntennaPatternGains


class AntennaGainCalculatorGainPattern(AntennaGainCalculator):
    def _calculate_gains_in_direction(self, azimuth: float) -> numpy.ndarray:
        return GetAntennaPatternGains(hor_dirs=self._bearings,
                                      ant_azimuth=azimuth,
                                      hor_pattern=self._dpa.gain_pattern)
