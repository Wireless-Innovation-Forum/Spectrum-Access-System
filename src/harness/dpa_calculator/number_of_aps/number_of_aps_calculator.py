from abc import abstractmethod


class NumberOfApsCalculator:
    def __init__(self, simulation_population: int):
        self._simulation_population = simulation_population

    @abstractmethod
    def get_number_of_aps(self) -> int:
        raise NotImplementedError
