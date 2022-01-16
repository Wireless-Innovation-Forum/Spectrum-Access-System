from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isclose
from typing import Any, List, TypeVar

RETURN_TYPE = TypeVar('RETURN_TYPE')


@dataclass
class FractionalDistribution:
    fraction: float
    range_maximum: float
    range_minimum: float

    def assert_data_matches_distribution(self, data: List[float], leeway_endpoint: float = 0.05, leeway_fraction: float = 0.001) -> None:
        data_within_range = [datum for datum in data if self.range_minimum <= datum <= self.range_maximum]
        fraction_within_range = len(data_within_range) / len(data)
        lowest = min(data_within_range)
        highest = max(data_within_range)
        assert isclose(lowest, self.range_minimum, abs_tol=leeway_endpoint), f'{lowest} != {self.range_minimum}'
        assert isclose(highest, self.range_maximum, abs_tol=leeway_endpoint), f'{highest} != {self.range_maximum}'
        assert isclose(fraction_within_range, self.fraction, abs_tol=leeway_fraction), \
            f'Range: {self.range_minimum}-{self.range_maximum}, Percentage: {fraction_within_range} != {self.fraction}'


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
