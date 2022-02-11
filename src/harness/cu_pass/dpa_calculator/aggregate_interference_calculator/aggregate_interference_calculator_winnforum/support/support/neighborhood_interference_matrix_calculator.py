from typing import List, Tuple

import numpy
from cached_property import cached_property

INTERFERENCE_MATRIX_INFO_TYPE = Tuple[numpy.ndarray, List[int], numpy.ndarray]


class NeighborhoodInterferenceMatrixCalculator:
    def __init__(self,
                 interference_matrix_info: INTERFERENCE_MATRIX_INFO_TYPE,
                 neighbor_grant_indexes: List[int]):
        self._interference_matrix_info = interference_matrix_info
        self._neighbor_grant_indexes = neighbor_grant_indexes

    def calculate(self) -> INTERFERENCE_MATRIX_INFO_TYPE:
        return self._neighborhood_interference_matrix, \
               self._neighborhood_grant_indexes_sorted_by_interference, \
               self._neighborhood_bearings

    @cached_property
    def _neighborhood_interference_matrix(self) -> numpy.ndarray:
        return numpy.asarray(self._neighborhood_grant_interferences).transpose()

    @cached_property
    def _neighborhood_grant_interferences(self) -> List[numpy.ndarray]:
        return [self._interference_matrix_by_grant[index]
                for index in self._interference_matrix_indexes_inside_neighborhood]

    @cached_property
    def _interference_matrix_by_grant(self) -> numpy.ndarray:
        return self._interference_matrix.transpose()

    @cached_property
    def _interference_matrix(self) -> numpy.ndarray:
        return self._interference_matrix_info[0]

    @cached_property
    def _neighborhood_grant_indexes_sorted_by_interference(self) -> List[int]:
        return [self._grant_index_sorted_by_interference[grant_index]
                for grant_index in self._interference_matrix_indexes_inside_neighborhood]

    @cached_property
    def _neighborhood_bearings(self) -> numpy.ndarray:
        return numpy.asarray([self._interference_bearings[index]
                              for index in self._interference_matrix_indexes_inside_neighborhood])

    @cached_property
    def _interference_matrix_indexes_inside_neighborhood(self) -> List[int]:
        return [interference_matrix_index
                for interference_matrix_index, grant_index in enumerate(self._grant_index_sorted_by_interference)
                if grant_index in self._neighbor_grant_indexes]

    @cached_property
    def _grant_index_sorted_by_interference(self) -> List[int]:
        return self._interference_matrix_info[1]

    @cached_property
    def _interference_bearings(self) -> numpy.ndarray:
        return self._interference_matrix_info[2]
