from dataclasses import dataclass
from typing import List

from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.building_loss_distributor import \
    BuildingLossDistributor
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator import CbsdInterferenceCalculator, \
    InterferenceComponents
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.interference_at_azimuth_with_maximum_gain_calculator import \
    InterferenceAtAzimuthWithMaximumGainCalculator

CORRECTION = 30  # from equation (8) in NTIA TR-15-517


@dataclass
class InterferenceWithDistance:
    interference: float
    distance_in_kilometers: float


class AggregateInterferenceCalculatorNtia(AggregateInterferenceCalculator):
    def calculate(self, minimum_distance: float) -> float:
        total_interference = InterferenceAtAzimuthWithMaximumGainCalculator(minimum_distance=minimum_distance,
                                                                            interference_components=self.interference_information).calculate()
        return total_interference + CORRECTION

    @cached_property
    def interference_information(self) -> List[InterferenceComponents]:
        interference_components = [CbsdInterferenceCalculator(cbsd=cbsd, dpa=self._dpa).calculate() for cbsd in self._cbsds]
        grouped_by_building_loss = BuildingLossDistributor(interference_components=interference_components).distribute()
        return [item for items in grouped_by_building_loss for item in items]
