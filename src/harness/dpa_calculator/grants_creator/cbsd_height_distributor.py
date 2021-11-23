import random
from dataclasses import dataclass
from typing import List

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.utils import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers import Cbsd, get_cbsd_ap, CBSD_A_INDICATOR

OUTDOOR_AP_HEIGHT_IN_METERS = 6


@dataclass
class HeightDistribution:
    maximum_height_in_meters: int
    minimum_height_in_meters: int
    fraction_of_cbsds: float


class CbsdHeightDistributor:
    def __init__(self, cbsd_locations: List[Point], region_type: str):
        self._cbsd_locations = cbsd_locations
        self._region_type = region_type

    def get(self) -> List[Cbsd]:
        @dataclass
        class LocationWithHeight:
            height: float
            location: Point

        cbsds_locations_grouped_by_height = []
        for distribution in self._height_distribution:
            next_index = sum(len(height_group) for height_group in cbsds_locations_grouped_by_height)
            number_of_cbsds_at_this_height = round(len(self._cbsd_locations) * distribution.fraction_of_cbsds)
            height_group_elements = [LocationWithHeight(
                height=round((distribution.minimum_height_in_meters + random.random() * (
                        distribution.maximum_height_in_meters - distribution.minimum_height_in_meters)) * 2) / 2,
                location=location
            ) for location in self._cbsd_locations[next_index:next_index + number_of_cbsds_at_this_height]]
            cbsds_locations_grouped_by_height.append(height_group_elements)

        return [get_cbsd_ap(category=CBSD_A_INDICATOR, height=location_with_height.height, is_indoor=True,
                            location=location_with_height.location)
                for height_group in cbsds_locations_grouped_by_height
                for location_with_height in height_group]

    @property
    def _height_distribution(self) -> List[HeightDistribution]:
        if self._region_type == REGION_TYPE_RURAL:
            return [
                HeightDistribution(
                    maximum_height_in_meters=3,
                    minimum_height_in_meters=3,
                    fraction_of_cbsds=0.8
                ),
                HeightDistribution(
                    maximum_height_in_meters=6,
                    minimum_height_in_meters=6,
                    fraction_of_cbsds=0.2
                ),
            ]
        elif self._region_type == REGION_TYPE_SUBURBAN:
            return [
                HeightDistribution(
                    maximum_height_in_meters=3,
                    minimum_height_in_meters=3,
                    fraction_of_cbsds=0.7
                ),
                HeightDistribution(
                    maximum_height_in_meters=12,
                    minimum_height_in_meters=6,
                    fraction_of_cbsds=0.3
                )
            ]
        elif self._region_type == REGION_TYPE_URBAN:
            return [
                HeightDistribution(
                    maximum_height_in_meters=3,
                    minimum_height_in_meters=3,
                    fraction_of_cbsds=0.5
                ),
                HeightDistribution(
                    maximum_height_in_meters=18,
                    minimum_height_in_meters=6,
                    fraction_of_cbsds=0.5
                )
            ]
