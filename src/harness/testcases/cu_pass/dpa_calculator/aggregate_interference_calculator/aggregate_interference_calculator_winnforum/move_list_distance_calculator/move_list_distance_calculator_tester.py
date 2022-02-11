from abc import ABC, abstractmethod
from typing import List

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.support.move_list_distance_calculator import \
    MOVE_LIST_DISTANCES_TYPE, MoveListDistanceCalculator
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import \
    get_arbitrary_coordinates


class MoveListDistanceCalculatorTester(ABC):
    def test(self):
        calculator = MoveListDistanceCalculator(all_grants=self._all_grants,
                                                grant_distances=self._arbitrary_grant_distances,
                                                move_list_indexes=self._move_list_indexes)
        distances = calculator.calculate()
        assert all(distances[expected_category] == expected_distance
                   for expected_category, expected_distance in self._expected_distances.items())

    @property
    def _all_grants(self) -> List[CbsdGrantInfo]:
        return [cbsd.to_grant() for cbsd in self._arbitrary_cbsds]

    @property
    def _arbitrary_cbsds(self) -> List[Cbsd]:
        cbsd_list = [
            Cbsd(cbsd_category=CbsdCategories.A),
            Cbsd(cbsd_category=CbsdCategories.A),
            Cbsd(cbsd_category=CbsdCategories.A),
            Cbsd(cbsd_category=CbsdCategories.B),
            Cbsd(cbsd_category=CbsdCategories.B),
            Cbsd(cbsd_category=CbsdCategories.B),
        ]
        for cbsd in cbsd_list:
            cbsd.location = get_arbitrary_coordinates()
        return cbsd_list

    @property
    def _arbitrary_grant_distances(self) -> List[float]:
        return [1, 3, 5, 2, 4, 6]

    @property
    @abstractmethod
    def _move_list_indexes(self) -> List[int]:
        pass

    @property
    @abstractmethod
    def _expected_distances(self) -> MOVE_LIST_DISTANCES_TYPE:
        pass
