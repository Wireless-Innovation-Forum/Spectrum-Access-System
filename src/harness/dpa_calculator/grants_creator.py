import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from cached_property import cached_property

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_URBAN, REGION_TYPE_SUBURBAN
from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point, get_region_type
from reference_models.common.data import CbsdGrantInfo
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers import CBSD_A_INDICATOR, Cbsd, get_cbsd_ap


PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE = {
    REGION_TYPE_RURAL: 0.99,
    REGION_TYPE_SUBURBAN: 0.99,
    REGION_TYPE_URBAN: 0.8
}

OUTDOOR_AP_HEIGHT_IN_METERS = 6


@dataclass
class HeightDistribution:
    maximum_height_in_meters: int
    minimum_height_in_meters: int
    fraction_of_cbsds: float


class GrantsCreator:
    def __init__(self, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> List[CbsdGrantInfo]:
        return [ap.to_grant() for ap in self._all_cbsds]

    def write_to_kml(self, filepath: Path) -> None:
        with open(filepath, 'w') as file:
            file.write('''
                <?xml version="1.0" encoding="UTF-8"?>
                    <kml xmlns="http://www.opengis.net/kml/2.2">
                        <Folder>
                            <name>KML Circle Generator Output</name>
                                <visibility>1</visibility>
            ''')
            for cbsd in self._all_cbsds:
                file.write(f'''
                    <Placemark>
                        <Point>
                            <coordinates>{cbsd.location.longitude},{cbsd.location.latitude}</coordinates>
                        </Point>
                    </Placemark>
                ''')
            file.write('''
                </Folder>
                    </kml>
            ''')

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        @dataclass
        class LocationWithHeight:
            height: float
            location: Point

        cbsds_locations_grouped_by_height = []
        for distribution in self._height_distribution:
            next_index = sum(len(height_group) for height_group in cbsds_locations_grouped_by_height)
            number_of_cbsds_at_this_height = round(len(self._indoor_cbsd_locations) * distribution.fraction_of_cbsds)
            height_group_elements = [LocationWithHeight(
                height=round((distribution.minimum_height_in_meters + random.random() * (distribution.maximum_height_in_meters - distribution.minimum_height_in_meters)) * 2) / 2,
                location=location
            ) for location in self._indoor_cbsd_locations[next_index:next_index + number_of_cbsds_at_this_height]]
            cbsds_locations_grouped_by_height.append(height_group_elements)

        return [get_cbsd_ap(category=CBSD_A_INDICATOR, height=location_with_height.height, is_indoor=True, location=location_with_height.location)
                for height_group in cbsds_locations_grouped_by_height
                for location_with_height in height_group]

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[:self._number_of_indoor_cbsds]

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

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, height=OUTDOOR_AP_HEIGHT_IN_METERS, is_indoor=False, location=location)
                for location in self._outdoot_cbsd_locations]

    @property
    def _outdoot_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[self._number_of_indoor_cbsds:]

    @cached_property
    def _distributed_cbsds(self) -> List[Point]:
        return PointDistributor(distribution_area=self._dpa_zone).distribute_points(number_of_points=self._number_of_cbsds)

    @property
    def _number_of_indoor_cbsds(self) -> int:
        return int(self._number_of_cbsds * self._percentage_of_indoor_aps)

    @property
    def _percentage_of_indoor_aps(self) -> float:
        return PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE[self._region_type]

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._dpa_zone.center_coordinates)
