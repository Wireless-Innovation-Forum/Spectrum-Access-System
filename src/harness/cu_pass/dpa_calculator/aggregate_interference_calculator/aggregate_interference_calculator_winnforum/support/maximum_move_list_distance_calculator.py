from typing import List, Tuple

import numpy

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import find_nc

THRESHOLD_MARGIN = 1
WINNFORUM_MINIMUM_INTERFERENCE = -1000


class MaximumMoveListDistanceCalculator:
    def __init__(self,
                 dpa: Dpa,
                 grant_distances: List[float],
                 grants_with_inband_frequencies: List[CbsdGrantInfo],
                 interference_matrix_info: Tuple[numpy.ndarray, List[int], numpy.ndarray],
                 neighbor_grants_info: Tuple[List[CbsdGrantInfo], List[int]]):
        self._dpa = dpa
        self._grant_distances = grant_distances
        self._grants_with_inband_frequencies = grants_with_inband_frequencies
        self._interference_matrix_info = interference_matrix_info
        self._neighbor_grants_info = neighbor_grants_info

    def calculate(self) -> float:
        interference_matrix_by_grant = self._interference_matrix.transpose()
        neighborhood_grant_interferences = [interference_matrix_by_grant[index]
                                            for index in self._neighborhood_grant_indexes_sorted_by_interference]
        neighborhood_bearings = [self._interference_bearings[index] for index in
                                 self._neighborhood_grant_indexes_sorted_by_interference]
        neighborhood_interference_matrix = numpy.asarray(neighborhood_grant_interferences).transpose()
        cutoff_index = find_nc(
            I=neighborhood_interference_matrix,
            bearings=neighborhood_bearings,
            t=self._dpa.threshold - THRESHOLD_MARGIN,
            beamwidth=self._dpa.beamwidth,
            min_azimuth=self._dpa.azimuth_range[0],
            max_azimuth=self._dpa.azimuth_range[1]) if len(neighborhood_interference_matrix) else len(
            self._neighborhood_grant_indexes_sorted_by_interference)
        move_list_indexes = self._neighborhood_grant_indexes_sorted_by_interference[cutoff_index:]
        move_grants = [self._grants_with_inband_frequencies[index] for index in move_list_indexes]
        move_grants_indexes_category_b = [move_list_indexes[index] for index, grant in enumerate(move_grants) if
                                          grant.cbsd_category == CbsdCategories.B.name]
        return max(self._grant_distances[index] for index in
                   move_grants_indexes_category_b) if move_grants_indexes_category_b else WINNFORUM_MINIMUM_INTERFERENCE

    @property
    def _interference_matrix(self) -> numpy.ndarray:
        return self._interference_matrix_info[0]

    @property
    def _neighborhood_grant_indexes_sorted_by_interference(self) -> List[int]:
        return [grant_index for grant_index in self._grant_index_sorted_by_interference if grant_index in self._neighbor_grant_indexes]

    @property
    def _grant_index_sorted_by_interference(self) -> List[int]:
        return self._interference_matrix_info[1]

    @property
    def _neighbor_grant_indexes(self) -> List[int]:
        return self._neighbor_grants_info[1]

    @property
    def _neighbor_grants(self) -> List[CbsdGrantInfo]:
        return self._neighbor_grants_info[0]

    @property
    def _low_inband_frequency(self) -> float:
        return self._grants_with_inband_frequencies[0].low_frequency

    @property
    def _high_inband_frequency(self) -> float:
        return self._grants_with_inband_frequencies[0].high_frequency

    @property
    def _interference_bearings(self) -> numpy.ndarray:
        return self._interference_matrix_info[2]
