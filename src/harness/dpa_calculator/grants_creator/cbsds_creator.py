from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Type

from cached_property import cached_property

from dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CBSD_A_INDICATOR, CbsdGetter
from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_URBAN, \
    REGION_TYPE_SUBURBAN
from dpa_calculator.grants_creator.cbsd_height_distributor.cbsd_height_distributor import CbsdHeightDistributor
from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utilities import Point, get_region_type
from reference_models.common.data import CbsdGrantInfo
from dpa_calculator.cbsd.cbsd import Cbsd

PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE = {
    REGION_TYPE_DENSE_URBAN: 0.8,
    REGION_TYPE_RURAL: 0.99,
    REGION_TYPE_SUBURBAN: 0.99,
    REGION_TYPE_URBAN: 0.8
}

UE_PER_AP_BY_REGION_TYPE = {
    REGION_TYPE_DENSE_URBAN: 50,
    REGION_TYPE_RURAL: 3,
    REGION_TYPE_SUBURBAN: 20,
    REGION_TYPE_URBAN: 50
}


class CbsdsCreator(ABC):
    def __init__(self, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> List[Cbsd]:
        return self._all_cbsds

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
        cbsd_locations_grouped_by_height = self._cbsd_height_distributor_class(cbsd_locations=self._indoor_cbsd_locations,
                                                                               region_type=self._region_type).get()
        return [self._cbsd_getter_class(category=CBSD_A_INDICATOR,
                                        height=location_with_height.height,
                                        is_indoor=True,
                                        location=location_with_height.location).get()
                for height_group in cbsd_locations_grouped_by_height
                for location_with_height in height_group]

    @property
    @abstractmethod
    def _cbsd_height_distributor_class(self) -> Type[CbsdHeightDistributor]:
        raise NotImplementedError

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[:self._number_of_indoor_cbsds]

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [self._cbsd_getter_class(category=CBSD_A_INDICATOR,
                                        height=self._outdoor_antenna_height,
                                        is_indoor=False,
                                        location=location).get()
                for location in self._outdoot_cbsd_locations]

    @property
    @abstractmethod
    def _outdoor_antenna_height(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def _cbsd_getter_class(self) -> Type[CbsdGetter]:
        raise NotImplementedError

    @property
    def _outdoot_cbsd_locations(self) -> List[Point]:
        return self._distributed_cbsds[self._number_of_indoor_cbsds:]

    @cached_property
    def _distributed_cbsds(self) -> List[Point]:
        return PointDistributor(distribution_area=self._dpa_zone)\
            .distribute_points(number_of_points=self._number_of_cbsds)

    @property
    def _number_of_indoor_cbsds(self) -> int:
        return round(self._number_of_cbsds * self._percentage_of_indoor_aps)

    @property
    def _percentage_of_indoor_aps(self) -> float:
        return PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE[self._region_type]

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._dpa_zone.center_coordinates)
