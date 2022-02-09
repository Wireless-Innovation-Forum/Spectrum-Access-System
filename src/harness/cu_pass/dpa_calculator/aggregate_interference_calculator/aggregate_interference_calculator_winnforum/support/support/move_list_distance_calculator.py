from collections import defaultdict
from typing import Dict, List

from cached_property import cached_property

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from reference_models.common.data import CbsdGrantInfo

MOVE_LIST_DISTANCES_TYPE = Dict[CbsdCategories, float]
MINIMUM_DISTANCE = 0


class MoveListDistanceCalculator:
    def __init__(self,
                 all_grants: List[CbsdGrantInfo],
                 grant_distances: List[float],
                 move_list_indexes: List[int]):
        self._all_grants = all_grants
        self._grant_distances = grant_distances
        self._move_list_indexes = move_list_indexes

    def calculate(self) -> MOVE_LIST_DISTANCES_TYPE:
        distances: MOVE_LIST_DISTANCES_TYPE = defaultdict(lambda: MINIMUM_DISTANCE)
        for cbsd_category, move_indexes in self._cbsd_category_move_grant_indexes.items():
            distances[cbsd_category] = max(self._grant_distances[index] for index in move_indexes)
        return distances

    @cached_property
    def _cbsd_category_move_grant_indexes(self) -> Dict[CbsdCategories, List[int]]:
        move_grant_indexes = defaultdict(list)
        for index, grant in enumerate(self._move_grants):
            cbsd_category = CbsdCategories[grant.cbsd_category]
            move_grant_indexes[cbsd_category].append(self._move_list_indexes[index])
        return move_grant_indexes

    @cached_property
    def _move_grants(self) -> List[CbsdGrantInfo]:
        return [self._all_grants[index] for index in self._move_list_indexes]