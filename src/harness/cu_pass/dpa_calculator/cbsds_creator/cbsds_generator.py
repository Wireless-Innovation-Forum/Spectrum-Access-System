from abc import ABC
from dataclasses import dataclass
from typing import List

from cached_property import cached_property

from cu_pass.dpa_calculator.cbsd.cbsd_builder.cbsd_builder import CbsdBuilder
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_distributor import CbsdHeightDistributor
from cu_pass.dpa_calculator.point_distributor import AreaCircle, CoordinatesWithBearing, PointDistributor
from cu_pass.dpa_calculator.utilities import get_region_type
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories, CbsdTypes


@dataclass
class CbsdsWithBearings:
    bearings: List[float]
    cbsds: List[Cbsd]


class CbsdsGenerator(ABC):
    def __init__(self,
                 cbsd_category: CbsdCategories,
                 cbsd_type: CbsdTypes,
                 dpa_zone: AreaCircle,
                 number_of_cbsds: int):
        self._cbsd_category = cbsd_category
        self._cbsd_type = cbsd_type
        self._dpa_zone = dpa_zone
        self._number_of_cbsds = number_of_cbsds

    def create(self) -> CbsdsWithBearings:
        return CbsdsWithBearings(
            bearings=self._bearings,
            cbsds=self._all_cbsds
        )

    @property
    def _all_cbsds(self) -> List[Cbsd]:
        return self._indoor_cbsds + self._outdoor_cbsds

    @property
    def _indoor_cbsds(self) -> List[Cbsd]:
        return self._generate_cbsds(is_indoor=True)

    @property
    def _outdoor_cbsds(self) -> List[Cbsd]:
        return self._generate_cbsds(is_indoor=False)

    def _generate_cbsds(self, is_indoor: bool) -> List[Cbsd]:
        cbsd_locations_grouped_by_height = CbsdHeightDistributor(cbsd_category=self._cbsd_category,
                                                                 cbsd_locations_and_bearings=self._distributed_cbsd_locations_with_bearings,
                                                                 cbsd_type=self._cbsd_type,
                                                                 is_indoor=is_indoor,
                                                                 region_type=self._region_type).distribute()
        return [CbsdBuilder(category=self._cbsd_category,
                            cbsd_type=self._cbsd_type,
                            dpa_region_type=self._region_type,
                            height=location_with_height.height,
                            is_indoor=is_indoor,
                            location=location_with_height.location).get()
                for height_group in cbsd_locations_grouped_by_height
                for location_with_height in height_group]

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
