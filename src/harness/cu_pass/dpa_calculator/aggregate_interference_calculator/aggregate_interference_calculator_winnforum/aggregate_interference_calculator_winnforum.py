import logging
from functools import partial
from math import inf
from typing import List, Tuple

import numpy
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.support.maximum_move_list_distance_calculator import \
    MaximumMoveListDistanceCalculator
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.utilities import get_distance_between_two_points, get_dpa_calculator_logger, get_dpa_center, \
    Point
from reference_models.common import mpool
from reference_models.common.data import CbsdGrantInfo, ProtectedEntityType, ProtectionConstraint
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import DpaType, findGrantsInsideNeighborhood, formInterferenceMatrix, \
    HIGH_FREQ_COCH, \
    LOW_FREQ_COCH

COCHANNEL_BANDWIDTH_IN_MEGAHERTZ = 10
HERTZ_IN_MEGAHERTZ = 1e6


class AggregateInterferenceCalculatorWinnforum(AggregateInterferenceCalculator):
    def calculate(self, distance: float, cbsd_category: CbsdCategories) -> float:
        maximum_move_distance_calculator = self._get_maximum_move_distance_calculator(distance, cbsd_category)
        return maximum_move_distance_calculator.get_max_distance()[cbsd_category]

    def get_expected_interference(self, distance: float, cbsd_category: CbsdCategories) -> float:
        maximum_move_distance_calculator = self._get_maximum_move_distance_calculator(neighborhood_distance=distance,
                                                                                      cbsd_category=cbsd_category)
        self._logger.info(f'\t\tThreshold used: {maximum_move_distance_calculator.interference_threshold} dBm')
        self._log_beamwidth()
        return maximum_move_distance_calculator.get_expected_interference()

    def _log_beamwidth(self) -> None:
        self._logger.info(f'\t\tBeamwidth: {self._dpa.beamwidth} degrees')

    @property
    def _logger(self) -> logging.Logger:
        return get_dpa_calculator_logger()

    def _get_maximum_move_distance_calculator(self,
                                              neighborhood_distance: float,
                                              cbsd_category: CbsdCategories) -> MaximumMoveListDistanceCalculator:
        neighbor_grants_info = self._get_neighbor_grants_info(neighborhood_distance=neighborhood_distance,
                                                              cbsd_category=cbsd_category)
        return MaximumMoveListDistanceCalculator(
            dpa=self._dpa,
            grant_distances=self._grant_distances,
            grants_with_inband_frequencies=self._grants_with_inband_frequencies,
            interference_matrix_info=self._interference_matrix_info,
            neighbor_grants_info=neighbor_grants_info)

    def _get_neighbor_grants_info(self, neighborhood_distance: float, cbsd_category: CbsdCategories) -> Tuple[List[CbsdGrantInfo], List[int]]:
        neighbor_distances = (inf, neighborhood_distance, 0, 0) \
            if cbsd_category == CbsdCategories.B \
            else (neighborhood_distance, inf, 0, 0)
        return findGrantsInsideNeighborhood(
            grants=self._grants_with_inband_frequencies,
            constraint=self._protection_constraint,
            dpa_type=self._dpa_type,
            neighbor_distances=neighbor_distances)

    @cached_property
    def _interference_matrix_info(self) -> Tuple[numpy.ndarray, List[int], numpy.ndarray]:
        grant_indexes = list(range(len(self._grants_with_inband_frequencies)))
        return formInterferenceMatrix(
            grants=self._grants_with_inband_frequencies,
            grants_ids=grant_indexes,
            constraint=self._protection_constraint,
            inc_ant_height=self._dpa.radar_height,
            num_iter=Dpa.num_iteration,
            dpa_type=self._dpa_type)

    @cached_property
    def _grant_distances(self) -> List[float]:
        pool = mpool.Pool()
        distanceFunction = partial(
            get_distance_between_two_points,
            point2=self._dpa_center)

        return pool.map(distanceFunction, [Point(latitude=grant.latitude, longitude=grant.longitude) for grant in self._grants_with_inband_frequencies])

    @cached_property
    def _grants_with_inband_frequencies(self) -> List[CbsdGrantInfo]:
        """
        Set inband frequency to 1 MHz to avoid scaling, since EIRPs are already given per 10 MHz
        """
        return [grant._replace(low_frequency=self._low_inband_frequency,
                               high_frequency=self._high_inband_frequency)
                for index, grant in enumerate(self._grants)]

    @property
    def _high_inband_frequency(self) -> float:
        return self._low_inband_frequency + self._frequency_in_hertz(COCHANNEL_BANDWIDTH_IN_MEGAHERTZ)

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
