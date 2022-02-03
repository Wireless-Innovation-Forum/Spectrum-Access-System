from dataclasses import dataclass
from typing import List, Tuple

import numpy
from cached_property import cached_property

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import find_nc, MINIMUM_INTERFERENCE_WINNFORUM

THRESHOLD_MARGIN = 1
MINIMUM_DISTANCE = 0


@dataclass
class CutoffIndexWithInterference:
    cutoff_index: int
    interference: float


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

    def get_max_distance(self) -> float:
        cbsd_category_move_grant_indexes = self._get_cbsd_category_move_grant_indexes(cbsd_category=CbsdCategories.B)
        return max(self._grant_distances[index] for index in cbsd_category_move_grant_indexes) \
            if cbsd_category_move_grant_indexes \
            else MINIMUM_DISTANCE

    def _get_cbsd_category_move_grant_indexes(self, cbsd_category: CbsdCategories) -> List[int]:
        return [self._move_list_indexes[index]
                for index, grant in enumerate(self._move_grants)
                if grant.cbsd_category == cbsd_category.name]

    @cached_property
    def _move_grants(self) -> List[CbsdGrantInfo]:
        return [self._grants_with_inband_frequencies[index] for index in self._move_list_indexes]

    @cached_property
    def _move_list_indexes(self) -> List[int]:
        return self._neighborhood_grant_indexes_sorted_by_interference[self._cutoff_index:]

    @cached_property
    def _cutoff_index(self) -> int:
        return self._cutoff_index_with_interference.cutoff_index

    def get_expected_interference(self) -> float:
        return self._cutoff_index_with_interference.interference

    @cached_property
    def _cutoff_index_with_interference(self) -> CutoffIndexWithInterference:
        cutoff_index, interference = find_nc(
            I=self._neighborhood_interference_matrix,
            bearings=self._neighborhood_bearings,
            t=self._dpa.threshold - THRESHOLD_MARGIN,
            beamwidth=self._dpa.beamwidth,
            min_azimuth=self._dpa.azimuth_range[0],
            max_azimuth=self._dpa.azimuth_range[1]
        ) if len(self._neighborhood_interference_matrix) \
            else self._default_cutoff_with_interference
        return CutoffIndexWithInterference(
            cutoff_index=cutoff_index,
            interference=interference
        )

    @cached_property
    def _neighborhood_interference_matrix(self) -> numpy.ndarray:
        return numpy.asarray(self._neighborhood_grant_interferences).transpose()

    @cached_property
    def _neighborhood_bearings(self) -> List[float]:
        return [self._interference_bearings[index] for index in
                self._interference_matrix_indexes_inside_neighborhood]

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
    def _default_cutoff_with_interference(self) -> Tuple[int, float]:
        return len(self._interference_matrix_indexes_inside_neighborhood), MINIMUM_INTERFERENCE_WINNFORUM

    @cached_property
    def _neighborhood_grant_indexes_sorted_by_interference(self) -> List[int]:
        return [self._grant_index_sorted_by_interference[grant_index]
                for grant_index in self._interference_matrix_indexes_inside_neighborhood]

    @cached_property
    def _interference_matrix_indexes_inside_neighborhood(self) -> List[int]:
        return [interference_matrix_index
                for interference_matrix_index, grant_index in enumerate(self._grant_index_sorted_by_interference)
                if grant_index in self._neighbor_grant_indexes]

    @cached_property
    def _grant_index_sorted_by_interference(self) -> List[int]:
        return self._interference_matrix_info[1]

    @cached_property
    def _neighbor_grant_indexes(self) -> List[int]:
        return self._neighbor_grants_info[1]

    @cached_property
    def _neighbor_grants(self) -> List[CbsdGrantInfo]:
        return self._neighbor_grants_info[0]

    @cached_property
    def _low_inband_frequency(self) -> float:
        return self._grants_with_inband_frequencies[0].low_frequency

    @cached_property
    def _high_inband_frequency(self) -> float:
        return self._grants_with_inband_frequencies[0].high_frequency

    @cached_property
    def _interference_bearings(self) -> numpy.ndarray:
        return self._interference_matrix_info[2]
