from typing import List

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.support.move_list_distance_calculator import \
    MINIMUM_DISTANCE, MOVE_LIST_DISTANCES_TYPE
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.move_list_distance_calculator.move_list_distance_calculator_tester import \
    MoveListDistanceCalculatorTester


class TestSomeCategoryDoesNotExist(MoveListDistanceCalculatorTester):
    @property
    def _move_list_indexes(self) -> List[int]:
        return [2]

    @property
    def _expected_distances(self) -> MOVE_LIST_DISTANCES_TYPE:
        return {
            CbsdCategories.A: 5,
            CbsdCategories.B: MINIMUM_DISTANCE,
        }
