from abc import abstractmethod
from dataclasses import dataclass

from cu_pass.dpa_calculator.utilities import Point


@dataclass
class NumberOfApsForPopulation:
    category_a: int
    category_b: int


class NumberOfApsCalculator:
    def __init__(self, center_coordinates: Point, simulation_population: int):
        self._center_coordinates = center_coordinates
        self._simulation_population = simulation_population

    @abstractmethod
    def get_number_of_aps(self) -> NumberOfApsForPopulation:
        raise NotImplementedError
