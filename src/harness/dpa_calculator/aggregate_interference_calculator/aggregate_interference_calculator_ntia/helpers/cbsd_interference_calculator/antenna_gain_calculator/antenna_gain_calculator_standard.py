from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from reference_models.antenna.antenna import GetStandardAntennaGains


class AntennaGainCalculatorStandard(AntennaGainCalculator):
    def _calculate_gain_in_direction(self, azimuth: float) -> float:
        return GetStandardAntennaGains(hor_dirs=self._bearing,
                                       ant_azimuth=azimuth,
                                       ant_beamwidth=self._dpa.beamwidth)
