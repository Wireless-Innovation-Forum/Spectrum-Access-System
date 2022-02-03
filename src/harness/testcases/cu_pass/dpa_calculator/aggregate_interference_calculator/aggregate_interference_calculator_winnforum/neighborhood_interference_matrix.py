from typing import List, Tuple

import numpy

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.support.neighborhood_interference_matrix_calculator import \
    INTERFERENCE_MATRIX_INFO_TYPE, NeighborhoodInterferenceMatrixCalculator
from reference_models.common.data import CbsdGrantInfo


class TestNeighborhoodInterferenceMatrix:
    def test(self):
        neighborhood_interference_matrix, sorted_neighborhood_indexes, neighborhood_bearings = NeighborhoodInterferenceMatrixCalculator(
            interference_matrix_info=self._interference_matrix_info,
            neighbor_grant_indexes=[0, 2]).calculate()
        assert numpy.array_equal(neighborhood_interference_matrix, self._expected_matrix)
        assert sorted_neighborhood_indexes == [2, 0]
        assert numpy.array_equal(neighborhood_bearings, [1, 0])

    @property
    def _expected_matrix(self) -> numpy.ndarray:
        return numpy.asarray([[2, 3], [5, 6]])

    @property
    def _interference_matrix_info(self) -> INTERFERENCE_MATRIX_INFO_TYPE:
        return self._interference_matrix, self._sorted_grant_indexes, self._interference_bearings

    @property
    def _interference_matrix(self) -> numpy.ndarray:
        return numpy.asarray([[1, 2, 3], [4, 5, 6]])

    @property
    def _sorted_grant_indexes(self) -> List[int]:
        return [1, 2, 0]

    @property
    def _interference_bearings(self) -> numpy.ndarray:
        return numpy.asarray([2, 1, 0])
