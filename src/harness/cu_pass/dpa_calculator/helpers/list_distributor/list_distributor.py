from abc import ABC, abstractmethod
from typing import Any, List, TypeVar

from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution

RETURN_TYPE = TypeVar('RETURN_TYPE')


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
