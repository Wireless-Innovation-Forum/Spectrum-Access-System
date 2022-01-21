from abc import abstractmethod
from typing import Dict

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.utilities import Point


NUMBER_OF_APS_FOR_POPULATION_TYPE = Dict[CbsdCategories, int]


class NumberOfApsCalculator:
    def __init__(self, center_coordinates: Point, simulation_population: int):
        self._center_coordinates = center_coordinates
        self._simulation_population = simulation_population

    @abstractmethod
    def get_number_of_aps(self) -> NUMBER_OF_APS_FOR_POPULATION_TYPE:
        raise NotImplementedError
