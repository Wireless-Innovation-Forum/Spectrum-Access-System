from functools import partial
from typing import List, Tuple

import numpy
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.utilities import get_distance_between_two_points, get_dpa_center, Point
from reference_models.common import mpool
from reference_models.common.data import CbsdGrantInfo, ProtectedEntityType, ProtectionConstraint
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import DpaType, find_nc, findGrantsInsideNeighborhood, formInterferenceMatrix, \
    HIGH_FREQ_COCH, LOW_FREQ_COCH

COCHANNEL_BANDWIDTH = 10
HERTZ_IN_MEGAHERTZ = 1e6
THRESHOLD_MARGIN = 1


class AggregateInterferenceCalculatorWinnforum(AggregateInterferenceCalculator):
    def calculate(self, minimum_distance: float) -> float:
        self._dpa.neighbor_distances = (150, minimum_distance, 0, 0)
        return self._max_move_list_distance()

    def _max_move_list_distance(self) -> float:
        interference_matrix_by_grant = self._interference_matrix.transpose()
        neighborhood_grant_interferences = [interference_matrix_by_grant[index]
                                            for index in self._neighborhood_grant_indexes_sorted_by_interference]
        neighborhood_bearings = [self._interference_bearings[index] for index in self._neighborhood_grant_indexes_sorted_by_interference]
        neighborhood_interference_matrix = numpy.asarray(neighborhood_grant_interferences).transpose()
        cutoff_index = find_nc(
            I=neighborhood_interference_matrix,
            bearings=neighborhood_bearings,
            t=self._dpa.threshold - THRESHOLD_MARGIN,
            beamwidth=self._dpa.beamwidth,
            min_azimuth=self._dpa.azimuth_range[0],
            max_azimuth=self._dpa.azimuth_range[1]) if len(neighborhood_interference_matrix) else len(self._neighborhood_grant_indexes_sorted_by_interference)
        move_list_indexes = self._neighborhood_grant_indexes_sorted_by_interference[cutoff_index:]
        move_grants = [self._grants_with_inband_frequences[index] for index in move_list_indexes]
        move_grants_indexes_category_b = [move_list_indexes[index] for index, grant in enumerate(move_grants) if grant.cbsd_category == CbsdCategories.B.name]
        return max(self._grant_distances[index] for index in move_grants_indexes_category_b) if move_grants_indexes_category_b else 0

    @property
    def _interference_bearings(self) -> numpy.ndarray:
        return self._interference_matrix_info[2]

    @property
    def _neighborhood_grant_indexes_sorted_by_interference(self) -> List[int]:
        return [grant_index for grant_index in self._grant_index_sorted_by_interference if grant_index in self._neighbor_grant_indexes]

    @property
    def _grant_index_sorted_by_interference(self) -> List[int]:
        return self._interference_matrix_info[1]

    @property
    def _interference_matrix(self) -> numpy.ndarray:
        return self._interference_matrix_info[0]

    @cached_property
    def _interference_matrix_info(self) -> Tuple[numpy.ndarray, List[int], numpy.ndarray]:
        grant_indexes = list(range(len(self._grants_with_inband_frequences)))
        return formInterferenceMatrix(
            grants=self._grants_with_inband_frequences,
            grants_ids=grant_indexes,
            constraint=self._protection_constraint,
            inc_ant_height=self._dpa.radar_height,
            num_iter=Dpa.num_iteration,
            dpa_type=self._dpa_type)

    @cached_property
    def _grant_distances(self) -> List[float]:
        pool = mpool.Pool()
        moveListConstraint = partial(
            get_distance_between_two_points,
            point2=self._dpa_center)

        return pool.map(moveListConstraint, [Point(latitude=grant.latitude, longitude=grant.longitude) for grant in self._grants_with_inband_frequences])

    @property
    def _neighbor_grant_indexes(self) -> List[int]:
        return self._neighbor_grants_info[1]

    @property
    def _neighbor_grants(self) -> List[CbsdGrantInfo]:
        return self._neighbor_grants_info[0]

    @property
    def _neighbor_grants_info(self) -> Tuple[List[CbsdGrantInfo], List[int]]:
        return findGrantsInsideNeighborhood(
            grants=self._grants_with_inband_frequences,
            constraint=self._protection_constraint,
            dpa_type=self._dpa_type,
            neighbor_distances=self._dpa.neighbor_distances)

    @property
    def _protection_constraint(self) -> ProtectionConstraint:
        return ProtectionConstraint(latitude=self._dpa_center.latitude,
                                    longitude=self._dpa_center.longitude,
                                    low_frequency=self._low_inband_frequency,
                                    high_frequency=self._high_inband_frequency,
                                    entity_type=ProtectedEntityType.DPA)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)

    @property
    def _dpa_type(self) -> DpaType:
        return DpaType.CO_CHANNEL

    @property
    def _grants_with_inband_frequences(self) -> List[CbsdGrantInfo]:
        return [grant._replace(low_frequency=self._low_inband_frequency,
                               high_frequency=self._high_inband_frequency)
                for index, grant in enumerate(self._grants)]

    @property
    def _high_inband_frequency(self) -> float:
        return self._frequency_in_hertz(self._low_inband_frequency + COCHANNEL_BANDWIDTH)

    @property
    def _low_inband_frequency(self) -> float:
        return self._frequency_in_hertz(self._first_inband_channel[0])

    @property
    def _first_inband_channel(self) -> Tuple[float, float]:
        return next(channel for channel in self._dpa._channels if self._channel_is_cochannel(channel))

    def _channel_is_cochannel(self, channel: Tuple[float, float]) -> bool:
        return self._frequency_in_hertz(channel[0]) >= LOW_FREQ_COCH and self._frequency_in_hertz(channel[1]) <= HIGH_FREQ_COCH

    @staticmethod
    def _frequency_in_hertz(frequency_in_megahertz: float) -> float:
        return frequency_in_megahertz * HERTZ_IN_MEGAHERTZ

    @property
    def _grants(self) -> List[CbsdGrantInfo]:
        return [cbsd.to_grant() for cbsd in self._cbsds]
