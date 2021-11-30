from dataclasses import dataclass, replace
from typing import List

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.cbsd.cbsd_interference_calculator.cbsd_interference_calculator import CbsdInterferenceCalculator, \
    InterferenceComponents
from dpa_calculator.helpers.list_distributor import ListDistributor
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_fractional_distribution import \
    FractionalDistribution


class BuildingLossDistributor(ListDistributor):
    def __init__(self, interference_components: List[InterferenceComponents]):
        super().__init__(items_to_distribute=interference_components)

    def _modify_group(self, distribution: FractionalDistribution, group: List[InterferenceComponents]) -> List[InterferenceComponents]:
        return [replace(interference_component,
                        loss_building=distribution.range_minimum,
        ) for interference_component in group]

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        return [
            FractionalDistribution(
                range_maximum=20,
                range_minimum=20,
                fraction=0.2
            ),
            FractionalDistribution(
                range_maximum=15,
                range_minimum=15,
                fraction=0.6
            ),
            FractionalDistribution(
                range_maximum=10,
                range_minimum=10,
                fraction=0.2
            ),
        ]


class AggregateInterferenceCalculatorNtia(AggregateInterferenceCalculator):
    def calculate(self) -> float:
        point = Point.from_shapely(point_shapely=self._dpa.geometry.centroid)

    @property
    def interference_information(self) -> List[InterferenceComponents]:
        interference_components = [CbsdInterferenceCalculator(cbsd=cbsd, dpa=self._dpa).calculate() for cbsd in self._cbsds]
        grouped_by_building_loss = BuildingLossDistributor(interference_components=interference_components).distribute()
        return [item for items in grouped_by_building_loss for item in items]

