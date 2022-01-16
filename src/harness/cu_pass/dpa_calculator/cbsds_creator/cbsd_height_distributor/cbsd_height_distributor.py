import random
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import \
    fractional_distribution_to_height_distribution, HeightDistribution, \
    INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A, INDOOR_UE_HEIGHT_DISTRIBUTION, OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A, \
    OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_B, OUTDOOR_UE_HEIGHT_DISTRIBUTION
from cu_pass.dpa_calculator.helpers.list_distributor import FractionalDistribution, ListDistributor
from cu_pass.dpa_calculator.utilities import Point


@dataclass
class LocationWithHeight:
    height: float
    location: Point


class CbsdHeightDistributor(ListDistributor):
    def __init__(self, cbsd_locations: List[Point], is_indoor: bool, region_type: str):
        super().__init__(items_to_distribute=cbsd_locations)
        self._is_indoor = is_indoor
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
        height_distributions = self._height_distribution_map[self._region_type]
        return [distribution.to_fractional_distribution() for distribution in height_distributions]

    @property
    @abstractmethod
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        raise NotImplementedError


class CbsdHeightDistributorAccessPointCategoryA(CbsdHeightDistributor):
    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A if self._is_indoor else OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A


class CbsdHeightDistributorAccessPointCategoryB(CbsdHeightDistributor):
    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_B


class CbsdHeightDistributorUserEquipment(CbsdHeightDistributor):
    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_UE_HEIGHT_DISTRIBUTION if self._is_indoor else OUTDOOR_UE_HEIGHT_DISTRIBUTION
