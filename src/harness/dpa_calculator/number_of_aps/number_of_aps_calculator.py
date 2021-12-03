from abc import abstractmethod

from dpa_calculator.utilities import Point


class NumberOfApsCalculator:
    def __init__(self, center_coordinates: Point, simulation_population: int):
        self._center_coordinates = center_coordinates
        self._simulation_population = simulation_population

    @abstractmethod
    def get_number_of_aps(self) -> int:
        raise NotImplementedError
