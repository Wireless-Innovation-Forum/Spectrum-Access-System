from dataclasses import dataclass, replace
from typing import List

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.list_distributor import ListDistributor


@dataclass
class BuildingLossDistribution:
    loss_in_db: int
    fraction: float

    def to_fractional_distribution(self) -> FractionalDistribution:
        return FractionalDistribution(
            range_maximum=self.loss_in_db,
            range_minimum=self.loss_in_db,
            fraction=self.fraction
        )


BUILDING_LOSS_DISTRIBUTIONS = [
    BuildingLossDistribution(
        loss_in_db=15,
        fraction=1
    ),
]


class BuildingLossDistributor(ListDistributor):
    def __init__(self, interference_components: List[InterferenceComponents]):
        super().__init__(items_to_distribute=interference_components)

    def _modify_group(self, distribution: FractionalDistribution, group: List[InterferenceComponents]) -> List[InterferenceComponents]:
        building_loss_distribution = fractional_distribution_to_building_loss_distribution(distribution=distribution)
        return [replace(interference_component,
                        loss_building=building_loss_distribution.loss_in_db,
        ) for interference_component in group]

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        return [distribution.to_fractional_distribution() for distribution in BUILDING_LOSS_DISTRIBUTIONS]


def fractional_distribution_to_building_loss_distribution(distribution: FractionalDistribution) -> BuildingLossDistribution:
    return BuildingLossDistribution(
        loss_in_db=int(distribution.range_minimum),
        fraction=distribution.fraction
    )
