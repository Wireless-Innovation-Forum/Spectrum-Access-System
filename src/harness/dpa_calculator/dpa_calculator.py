from math import ceil


class NumberOfApsCalculatorGroundBased:
    _channel_scaling_factor = 1
    _market_penetration_factor = 0.4
    _outdoor_aps_ratio = 0.2

    def __init__(self, city_population: int, simulation_population: int):
        self._city_population = city_population
        self._simulation_population = simulation_population

    @property
    def number_of_aps(self) -> int:
        return ceil(self._number_of_aps_exact)

    @property
    def _number_of_aps_exact(self) -> float:
        return (self._city_population * self._market_penetration_factor * self._simulation_population_ratio * self._outdoor_aps_ratio * self._channel_scaling_factor) / 20

    @property
    def _simulation_population_ratio(self) -> float:
        return self._simulation_population / self._city_population
