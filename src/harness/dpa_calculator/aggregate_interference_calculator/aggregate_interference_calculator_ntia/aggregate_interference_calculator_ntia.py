import logging
from dataclasses import dataclass
from typing import List

from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.building_loss_distributor import \
    BuildingLossDistributor
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.cbsd_interference_calculator import CbsdInterferenceCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.interference_at_azimuth_with_maximum_gain_calculator import \
    InterferenceAtAzimuthWithMaximumGainCalculator
from dpa_calculator.cbsd.cbsd import Cbsd


@dataclass
class InterferenceWithDistance:
    interference: float
    distance_in_kilometers: float


class AggregateInterferenceCalculatorNtia(AggregateInterferenceCalculator):
    def calculate(self, minimum_distance: float = 0) -> float:
        total_interference = InterferenceAtAzimuthWithMaximumGainCalculator(minimum_distance=minimum_distance,
                                                                            interference_components=self.interference_information).calculate()
        return total_interference

    @cached_property
    def interference_information(self) -> List[InterferenceComponents]:
        interference_components = [self._get_interference_contribution(cbsd=cbsd, index=index) for index, cbsd in enumerate(self._cbsds)]
        grouped_by_building_loss = BuildingLossDistributor(interference_components=interference_components).distribute()
        return [item for items in grouped_by_building_loss for item in items]

    def _get_interference_contribution(self, cbsd: Cbsd, index: int) -> InterferenceComponents:
        logging.info(f'\tCBSD {index + 1} / {len(self._cbsds)}')
        cbsd_interference_calculator = self._get_cbsd_interference_calculator(cbsd=cbsd)
        return cbsd_interference_calculator.calculate()

    def _get_cbsd_interference_calculator(self, cbsd: Cbsd) -> CbsdInterferenceCalculator:
        return CbsdInterferenceCalculator(cbsd=cbsd, dpa=self._dpa, receive_antenna_gain_calculator_class=self._receive_antenna_gain_calculator_class)
