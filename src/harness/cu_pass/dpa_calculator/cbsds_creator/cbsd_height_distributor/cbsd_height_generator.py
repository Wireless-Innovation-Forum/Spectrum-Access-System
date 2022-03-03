import random
from dataclasses import dataclass
from typing import List

from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import \
    fractional_distribution_to_height_distribution, HeightDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.list_distributor import ListDistributor
from cu_pass.dpa_calculator.utilities import Point


@dataclass
class LocationWithHeight:
    height: float
    location: Point


class CbsdHeightGenerator(ListDistributor):
    def __init__(self,
                 cbsd_locations: List[Point],
                 region_type: str,
                 distributions: List[FractionalDistribution] = None):
        super().__init__(items_to_distribute=cbsd_locations)
        self.__distributions = distributions
        self._region_type = region_type

    def _modify_group(self, distribution: FractionalDistribution, group: List[Point]) -> List[LocationWithHeight]:
        height_distribution = fractional_distribution_to_height_distribution(distribution=distribution)
        return [LocationWithHeight(
            height=self._get_random_height(distribution=height_distribution),
            location=location
        ) for location in group]

    @staticmethod
    def _get_random_height(distribution: HeightDistribution) -> float:
        random_height = random.uniform(distribution.minimum_height_in_meters, distribution.maximum_height_in_meters)
        height_to_the_nearest_half_meter = round(random_height * 2) / 2
        return height_to_the_nearest_half_meter

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        return self.__distributions
