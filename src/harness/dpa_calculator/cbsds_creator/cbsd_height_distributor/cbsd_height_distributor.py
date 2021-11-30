import random
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import HeightDistribution, \
    INDOOR_AP_HEIGHT_DISTRIBUTION, INDOOR_UE_HEIGHT_DISTRIBUTION
from dpa_calculator.helpers.list_distributor import ListDistributor
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_fractional_distribution import \
    FractionalDistribution


@dataclass
class LocationWithHeight:
    height: float
    location: Point


class CbsdHeightDistributor(ListDistributor):
    def __init__(self, cbsd_locations: List[Point], region_type: str):
        super().__init__(items_to_distribute=cbsd_locations)
        self._region_type = region_type

    def _modify_group(self, distribution: FractionalDistribution, group: List[Point]) -> List[LocationWithHeight]:
        return [LocationWithHeight(
            height=self._get_random_height(distribution=distribution),
            location=location
        ) for location in group]

    @staticmethod
    def _get_random_height(distribution: FractionalDistribution) -> float:
        random_height = random.uniform(distribution.range_minimum, distribution.range_maximum)
        height_to_the_nearest_half_meter = round(random_height * 2) / 2
        return height_to_the_nearest_half_meter

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        height_distributions = self._height_distribution_map[self._region_type]
        return [
            FractionalDistribution(
                range_maximum=distribution.maximum_height_in_meters,
                range_minimum=distribution.minimum_height_in_meters,
                fraction=distribution.fraction_of_cbsds
            )
            for distribution in height_distributions
        ]

    @property
    @abstractmethod
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        raise NotImplementedError


class CbsdHeightDistributorAccessPoint(CbsdHeightDistributor):
    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_AP_HEIGHT_DISTRIBUTION


class CbsdHeightDistributorUserEquipment(CbsdHeightDistributor):
    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_UE_HEIGHT_DISTRIBUTION
