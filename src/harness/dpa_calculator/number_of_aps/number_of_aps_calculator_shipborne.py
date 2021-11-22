from dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsCalculator


class NumberOfApsCalculatorGroundBased(NumberOfApsCalculator):
    _channel_scaling_factor = 0.1
    _market_penetration_factor = 0.2
    _daytime_commuter_factor = 1.15

    def get_number_of_aps(self) -> int:
        return round(self._number_of_aps_exact)

    @property
    def _number_of_aps_exact(self) -> float:
        return (self._simulation_population * self._daytime_commuter_factor * self._market_penetration_factor * self._channel_scaling_factor) / 50
