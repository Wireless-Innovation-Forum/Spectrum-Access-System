import random
from dataclasses import dataclass
from typing import List

from dpa_calculator.grants_creator.height_distribution_definitions import HeightDistribution, \
    INDOOR_AP_HEIGHT_DISTRIBUTION
from dpa_calculator.utils import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers import Cbsd, get_cbsd_ap, CBSD_A_INDICATOR


@dataclass
class LocationWithHeight:
    height: float
    location: Point


class CbsdHeightDistributor:
    def __init__(self, cbsd_locations: List[Point], region_type: str):
        self._cbsd_locations = cbsd_locations
        self._region_type = region_type

    def get(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR,
                            height=location_with_height.height,
                            is_indoor=True,
                            location=location_with_height.location)
                for height_group in self._cbsd_locations_grouped_by_height
                for location_with_height in height_group]

    @property
    def _cbsd_locations_grouped_by_height(self) -> List[List[LocationWithHeight]]:
        cbsd_locations_grouped_by_height = []
        for distribution in self._height_distribution:
            next_index = sum(len(height_group) for height_group in cbsd_locations_grouped_by_height)
            remaining_cbsd_locations = self._cbsd_locations[next_index:]
            cbsd_locations_with_heights = self._generate_heights_for_distribution(distribution=distribution, cbsd_locations=remaining_cbsd_locations)
            cbsd_locations_grouped_by_height.append(cbsd_locations_with_heights)
        return cbsd_locations_grouped_by_height

    @property
    def _height_distribution(self) -> List[HeightDistribution]:
        return INDOOR_AP_HEIGHT_DISTRIBUTION[self._region_type]

    def _generate_heights_for_distribution(self, distribution: HeightDistribution, cbsd_locations: List[Point]) -> List[LocationWithHeight]:
        number_of_cbsds_at_this_height = round(self._total_number_of_cbsd_locations * distribution.fraction_of_cbsds)
        return [LocationWithHeight(
            height=self._get_random_height(distribution=distribution),
            location=location
        ) for location in cbsd_locations[:number_of_cbsds_at_this_height]]

    @property
    def _total_number_of_cbsd_locations(self) -> int:
        return len(self._cbsd_locations)

    @staticmethod
    def _get_random_height(distribution: HeightDistribution) -> float:
        height_range = distribution.maximum_height_in_meters - distribution.minimum_height_in_meters
        random_height = distribution.minimum_height_in_meters + random.random() * height_range
        height_to_the_nearest_half_meter = round(random_height * 2) / 2
        return height_to_the_nearest_half_meter
