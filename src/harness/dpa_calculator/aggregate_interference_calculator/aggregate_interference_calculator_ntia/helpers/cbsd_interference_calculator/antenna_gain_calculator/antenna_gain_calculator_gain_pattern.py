from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from reference_models.antenna.antenna import GetAntennaPatternGains


class AntennaGainCalculatorGainPattern(AntennaGainCalculator):
    def _calculate_gain_in_direction(self, azimuth: float) -> float:
        return GetAntennaPatternGains(hor_dirs=self._bearing,
                                      ant_azimuth=azimuth,
                                      hor_pattern=self._dpa.gain_pattern)
