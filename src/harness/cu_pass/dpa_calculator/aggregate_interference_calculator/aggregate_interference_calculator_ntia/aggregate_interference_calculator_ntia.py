import logging
from dataclasses import dataclass, replace
from typing import List

from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.building_loss_distributor import \
    BuildingLossDistributor
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.cbsd_interference_calculator import CbsdInterferenceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.interference_at_azimuth_with_maximum_gain_calculator import \
    InterferenceAtAzimuthWithMaximumGainCalculator
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger


@dataclass
class InterferenceWithDistance:
    interference: float
    distance_in_kilometers: float


class AggregateInterferenceCalculatorNtia(AggregateInterferenceCalculator):
    def calculate(self, distance: float = 0) -> float:
        total_interference = InterferenceAtAzimuthWithMaximumGainCalculator(minimum_distance=distance,
                                                                            interference_components=self.interference_components).calculate()
        return total_interference

    @cached_property
    def interference_components(self) -> List[InterferenceComponents]:
        interference_components = [self._get_interference_contribution(cbsd=cbsd, index=index) for index, cbsd in enumerate(self._cbsds)]
        interference_components = self._add_receiver_gains(interference_components=interference_components)
        interference_components = self._add_building_loss(interference_components=interference_components)
        return interference_components

    def _get_interference_contribution(self, cbsd: Cbsd, index: int) -> InterferenceComponents:
        logger = get_dpa_calculator_logger()
        logger.info(f'\tCBSD {index + 1} / {len(self._cbsds)}')
        cbsd_interference_calculator = CbsdInterferenceCalculator(cbsd=cbsd, dpa=self._dpa)
        return cbsd_interference_calculator.calculate()

    def _add_receiver_gains(self, interference_components: List[InterferenceComponents]) -> List[InterferenceComponents]:
        cbsd_gains = self._receive_antenna_gain_calculator_class(bearings=self._bearings, cbsds=self._cbsds, dpa=self._dpa).calculate()
        return [replace(interference_components[cbsd_number], gain_receiver=gain_receiver)
                for cbsd_number, gain_receiver in enumerate(cbsd_gains)]

    def _add_building_loss(self, interference_components: List[InterferenceComponents]) -> List[InterferenceComponents]:
        grouped_by_building_loss = BuildingLossDistributor(interference_components=interference_components).distribute()
        return [item for items in grouped_by_building_loss for item in items]
