from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isclose
from typing import List


@dataclass
class FractionalDistribution(ABC):
    fraction: float
    range_maximum: float
    range_minimum: float

    @abstractmethod
    def get_values(self, number_of_values: int) -> List[float]:
        pass

    @abstractmethod
    def assert_data_matches_distribution(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        pass

    def _assert_data_range(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        data_within_range = self.get_data_within_range(data=data)
        lowest = self.get_lowest(data=data)
        highest = self.get_highest(data=data)
        fraction_within_range = self.get_fraction_within_range(data=data)
        if self.range_minimum != self.range_maximum:
            assert len(set(data_within_range)) != 1, 'Data is not dispersed within range'
        assert lowest >= self.range_minimum, f'{lowest} < {self.range_minimum}'
        assert highest <= self.range_maximum, f'{highest} > {self.range_maximum}'
        assert isclose(fraction_within_range, self.fraction, abs_tol=leeway_fraction), \
            f'Range: {self.range_minimum}-{self.range_maximum}, Percentage: {fraction_within_range} != {self.fraction}'

    def get_lowest(self, data: List[float]) -> float:
        data_within_range = self.get_data_within_range(data=data)
        return min(data_within_range)

    def get_highest(self, data: List[float]) -> float:
        data_within_range = self.get_data_within_range(data=data)
        return max(data_within_range)

    def get_fraction_within_range(self, data: List[float]) -> float:
        data_within_range = self.get_data_within_range(data=data)
        return len(data_within_range) / len(data)

    def get_data_within_range(self, data: List[float]) -> List[float]:
        return [datum for datum in data if self.range_minimum <= datum <= self.range_maximum]
