from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from cached_property import cached_property

from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.geo.drive import nlcd_driver
from reference_models.geo.nlcd import GetRegionType
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers import CBSD_A_INDICATOR, Cbsd, get_cbsd_ap


@dataclass
class PercentageOfIndoorApsByRegionType:
    rural: float = 0.99
    suburban: float = 0.99
    urban: float = 0.8

    def __getitem__(self, item: str) -> float:
        return asdict(self)[item]


class GrantsCreator:
    def __init__(self, dpa: Dpa, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa = dpa
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> List[CbsdGrantInfo]:
        return [ap.to_grant() for ap in self._all_cbsds]

    def write_to_kml(self, filepath: Path) -> None:
        with open(filepath, 'w') as file:
            file.write('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Folder>
    <name>KML Circle Generator Output</name>
    <visibility>1</visibility>''')
            for cbsd in self._all_cbsds:
                file.write(f'''
                <Placemark>
                    <Point>
                        <coordinates>{cbsd.location.longitude},{cbsd.location.latitude}</coordinates>
                    </Point>
                </Placemark>
                ''')
            file.write('''</Folder>
</kml>''')

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=True, location=location)
                for location in self._indoor_cbsd_locations]

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[:self._number_of_indoor_cbsds]

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [get_cbsd_ap(category=CBSD_A_INDICATOR, is_indoor=False, location=location)
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
        return PercentageOfIndoorApsByRegionType()[self._region_type.lower()]

    @property
    def _region_type(self) -> str:
        cbsd_region_code = nlcd_driver.GetLandCoverCodes(
            self._dpa_zone.center_coordinates.latitude,
            self._dpa_zone.center_coordinates.longitude
        )
        return GetRegionType(cbsd_region_code)
