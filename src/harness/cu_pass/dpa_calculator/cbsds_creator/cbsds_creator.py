from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Type

from cached_property import cached_property

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CBSD_A_INDICATOR, CbsdGetter
from cu_pass.dpa_calculator.cbsds_creator.kml_writer import KmlWriter
from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_URBAN, \
    REGION_TYPE_SUBURBAN
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_distributor import CbsdHeightDistributor
from cu_pass.dpa_calculator.point_distributor import AreaCircle, CoordinatesWithBearing, PointDistributor
from cu_pass.dpa_calculator.utilities import Point, get_region_type
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd

PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE = {
    REGION_TYPE_DENSE_URBAN: 0.8,
    REGION_TYPE_RURAL: 0.99,
    REGION_TYPE_SUBURBAN: 0.99,
    REGION_TYPE_URBAN: 0.8
}


@dataclass
class CbsdsWithBearings:
    bearings: List[float]
    cbsds: List[Cbsd]


class CbsdsCreator(ABC):
    def __init__(self, dpa_zone: AreaCircle, number_of_cbsds: int):
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> CbsdsWithBearings:
        return CbsdsWithBearings(
            bearings=self._bearings,
            cbsds=self._all_cbsds
        )

    def write_to_kml(self, filepath: Path, distance_to_exclude: int = 0) -> None:
        KmlWriter(cbsds=self._all_cbsds,
                  output_filepath=filepath,
                  distance_to_exclude=distance_to_exclude,
                  dpa_center=self._dpa_zone.center_coordinates).write()

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        cbsd_locations_grouped_by_height = self._cbsd_height_distributor_class(cbsd_locations=self._indoor_cbsd_locations,
                                                                               region_type=self._region_type).distribute()
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
        return self._all_cbsd_locations[:self._number_of_indoor_cbsds]

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return [self._cbsd_getter_class(category=CBSD_A_INDICATOR,
                                        height=self._outdoor_antenna_height,
                                        is_indoor=False,
                                        location=location).get()
                for location in self._outdoor_cbsd_locations]

    @property
    @abstractmethod
    def _cbsd_getter_class(self) -> Type[CbsdGetter]:
        raise NotImplementedError

    @property
    @abstractmethod
    def _outdoor_antenna_height(self) -> float:
        raise NotImplementedError

    @property
    def _outdoor_cbsd_locations(self) -> List[Point]:
        return self._all_cbsd_locations[self._number_of_indoor_cbsds:]

    @property
    def _all_cbsd_locations(self) -> List[Point]:
        return [location_with_bearing.coordinates for location_with_bearing in self._distributed_cbsd_locations_with_bearings]

    @property
    def _number_of_indoor_cbsds(self) -> int:
        return round(self._number_of_cbsds * self._percentage_of_indoor_aps)

    @property
    def _percentage_of_indoor_aps(self) -> float:
        return PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE[self._region_type]

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._dpa_zone.center_coordinates)

    @property
    def _bearings(self) -> List[float]:
        return [location_with_bearing.bearing for location_with_bearing in self._distributed_cbsd_locations_with_bearings]

    @cached_property
    def _distributed_cbsd_locations_with_bearings(self) -> List[CoordinatesWithBearing]:
        return PointDistributor(distribution_area=self._dpa_zone)\
            .distribute_points(number_of_points=self._number_of_cbsds)
