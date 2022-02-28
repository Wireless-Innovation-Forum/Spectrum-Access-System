import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isclose
from statistics import mean, stdev
from typing import Any, List, TypeVar

import numpy
from numpy.random import default_rng
from scipy.stats import norm, normaltest, truncnorm

RETURN_TYPE = TypeVar('RETURN_TYPE')


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


@dataclass
class FractionalDistributionUniform(FractionalDistribution):
    def assert_data_matches_distribution(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        self._assert_data_range(data=data, leeway_fraction=leeway_fraction)

    def get_values(self, number_of_values: int) -> List[float]:
        return [random.uniform(self.range_minimum, self.range_maximum) for _ in range(number_of_values)]


@dataclass
class FractionalDistributionNormal(FractionalDistribution):
    mean: float
    standard_deviation: float

    def get_values(self, number_of_values: int) -> List[float]:
        lower_bound = (self.range_minimum - self.mean) / self.standard_deviation
        upper_bound = (self.range_maximum - self.mean) / self.standard_deviation
        generator = truncnorm(lower_bound, upper_bound, loc=self.mean, scale=self.standard_deviation)
        return generator.rvs(number_of_values).tolist()

    def assert_data_matches_distribution(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        self._assert_data_range(data=data, leeway_fraction=leeway_fraction)
        self._assert_normal_distribution(data=data, leeway_fraction=leeway_fraction)

    def _assert_normal_distribution(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        data_within_range = self.get_data_within_range(data=data)
        assert isclose(mean(data_within_range), self.mean, abs_tol=leeway_fraction), 'Mean does not match.'
        assert isclose(stdev(data_within_range), self.standard_deviation, abs_tol=leeway_fraction), 'Standard deviation does not match.'
        assert normaltest(data_within_range), 'Data is not normally distributed.'


class ListDistributor(ABC):
    def __init__(self, items_to_distribute: List[Any]):
        self._items = items_to_distribute

    def distribute(self) -> List[List[RETURN_TYPE]]:
        return [self._modify_group(distribution=distribution, group=group)
                for distribution, group in zip(self._distributions, self._groups)]

    @abstractmethod
    def _modify_group(self, distribution: FractionalDistribution, group: List[Any]) -> List[RETURN_TYPE]:
        return group

    @property
    def _groups(self) -> List[List[Any]]:
        groups = []
        for distribution in self._distributions:
            next_index = sum(len(group) for group in groups)
            remaining_items = self._items[next_index:]
            items_in_group = self._get_items_in_distribution(distribution=distribution, items=remaining_items)
            groups.append(items_in_group)
        return groups

    @property
    @abstractmethod
    def _distributions(self) -> List[FractionalDistribution]:
        raise NotImplementedError

    def _get_items_in_distribution(self, distribution: FractionalDistribution, items: List[Any]) -> List[Any]:
        number_at_this_distribution = round(self._total_number_of_items * distribution.fraction)
        is_last_distribution = distribution == self._distributions[-1]
        return items if is_last_distribution else items[:number_at_this_distribution]

    @property
    def _total_number_of_items(self) -> int:
        return len(self._items)
