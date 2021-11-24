from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsCalculator
from dpa_calculator.utilities import Point, get_region_type


REGION_TYPE_TO_DENOMINATOR = {
    REGION_TYPE_DENSE_URBAN: 50,
    REGION_TYPE_RURAL: 3,
    REGION_TYPE_SUBURBAN: 20,
    REGION_TYPE_URBAN: 50
}


class NumberOfApsCalculatorShipborne(NumberOfApsCalculator):
    _channel_scaling_factor = 0.1
    _daytime_commuter_factor = 1.15
    _market_penetration_factor = 0.2

    def __init__(self, center_coordinates: Point, simulation_population: int):
        super().__init__(simulation_population=simulation_population)
        self._center_coordinates = center_coordinates

    def get_number_of_aps(self) -> int:
        return round(self._number_of_aps_exact)

    @property
    def _number_of_aps_exact(self) -> float:
        return self._numerator / self._denominator

    @property
    def _numerator(self) -> float:
        return self._simulation_population * self._daytime_commuter_factor * self._market_penetration_factor * self._channel_scaling_factor

    @property
    def _denominator(self) -> int:
        return REGION_TYPE_TO_DENOMINATOR[self._region_type]

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._center_coordinates)
