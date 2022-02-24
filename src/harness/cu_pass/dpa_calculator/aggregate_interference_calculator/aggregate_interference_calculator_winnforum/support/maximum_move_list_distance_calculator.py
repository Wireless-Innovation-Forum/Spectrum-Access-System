from dataclasses import dataclass
from typing import List, Tuple

import numpy
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.support.move_list_distance_calculator import \
    MOVE_LIST_DISTANCES_TYPE, MoveListDistanceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.support.neighborhood_interference_matrix_calculator import \
    INTERFERENCE_MATRIX_INFO_TYPE, NeighborhoodInterferenceMatrixCalculator
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.move_list import find_nc, MINIMUM_INTERFERENCE_WINNFORUM

THRESHOLD_MARGIN = 1

NEIGHBOR_GRANTS_INFO_TYPE = Tuple[List[CbsdGrantInfo], List[int]]


@dataclass
class CutoffIndexWithInterference:
    cutoff_index: int
    interference: float


class MaximumMoveListDistanceCalculator:
    def __init__(self,
                 dpa: Dpa,
                 grant_distances: List[float],
                 grants_with_inband_frequencies: List[CbsdGrantInfo],
                 interference_matrix_info: INTERFERENCE_MATRIX_INFO_TYPE,
                 neighbor_grants_info: NEIGHBOR_GRANTS_INFO_TYPE):
        self._dpa = dpa
        self._grant_distances = grant_distances
        self._grants_with_inband_frequencies = grants_with_inband_frequencies
        self._interference_matrix_info = interference_matrix_info
        self._neighbor_grants_info = neighbor_grants_info

    def get_max_distance(self) -> MOVE_LIST_DISTANCES_TYPE:
        return self._move_list_distance_calculator.calculate()

    @cached_property
    def _move_list_distance_calculator(self) -> MoveListDistanceCalculator:
        return MoveListDistanceCalculator(all_grants=self._grants_with_inband_frequencies,
                                          grant_distances=self._grant_distances,
                                          move_list_indexes=self._move_list_indexes)

    @cached_property
    def _move_list_indexes(self) -> List[int]:
        return self._neighborhood_grant_indexes_sorted_by_ascending_interference[self._cutoff_index:]

    @cached_property
    def _cutoff_index(self) -> int:
        return self._cutoff_index_with_interference.cutoff_index

    def get_expected_interference(self) -> float:
        return self._cutoff_index_with_interference.interference

    @cached_property
    def _cutoff_index_with_interference(self) -> CutoffIndexWithInterference:
        cutoff_index, interference = find_nc(
            I=self._neighborhood_interference_matrix,
            bearings=self._neighborhood_grant_bearings,
            t=self.interference_threshold,
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
    def _default_cutoff_with_interference(self) -> Tuple[int, float]:
        return len(self._neighbor_grant_indexes), MINIMUM_INTERFERENCE_WINNFORUM

    @cached_property
    def _neighborhood_interference_matrix(self) -> numpy.ndarray:
        return self._neighborhood_interference_matrix_info[0]

    @cached_property
    def _neighborhood_grant_indexes_sorted_by_ascending_interference(self) -> List[int]:
        return self._neighborhood_interference_matrix_info[1]

    @cached_property
    def _neighborhood_grant_bearings(self) -> numpy.ndarray:
        return self._neighborhood_interference_matrix_info[2]

    @cached_property
    def _neighborhood_interference_matrix_info(self) -> INTERFERENCE_MATRIX_INFO_TYPE:
        return NeighborhoodInterferenceMatrixCalculator(interference_matrix_info=self._interference_matrix_info,
                                                        neighbor_grant_indexes=self._neighbor_grant_indexes).calculate()

    @cached_property
    def _neighbor_grant_indexes(self) -> List[int]:
        return self._neighbor_grants_info[1]

    @property
    def interference_threshold(self) -> int:
        return self._dpa.threshold + THRESHOLD_MARGIN
