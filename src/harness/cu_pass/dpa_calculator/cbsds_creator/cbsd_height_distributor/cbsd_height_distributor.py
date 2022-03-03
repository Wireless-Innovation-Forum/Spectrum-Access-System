from typing import List

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_distributions_factory import \
    CbsdHeightDistributionsFactory
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_generator import CbsdHeightGenerator, \
    LocationWithHeight
from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, \
    REGION_TYPE_URBAN
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.point_distributor import CoordinatesWithBearing
from cu_pass.dpa_calculator.utilities import Point

PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE_CATEGORY_A = {
    REGION_TYPE_DENSE_URBAN: 1,
    REGION_TYPE_RURAL: 1,
    REGION_TYPE_SUBURBAN: 1,
    REGION_TYPE_URBAN: 1
}
PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE_CATEGORY_B = {
    REGION_TYPE_DENSE_URBAN: 0,
    REGION_TYPE_RURAL: 0,
    REGION_TYPE_SUBURBAN: 0,
    REGION_TYPE_URBAN: 0
}


class CbsdHeightDistributor:
    def __init__(self,
                 cbsd_category: CbsdCategories,
                 cbsd_locations_and_bearings: List[CoordinatesWithBearing],
                 cbsd_type: CbsdTypes,
                 is_indoor: bool,
                 region_type: str):
        self._cbsd_category = cbsd_category
        self._cbsd_locations_and_bearings = cbsd_locations_and_bearings
        self._cbsd_type = cbsd_type
        self._is_indoor = is_indoor
        self._region_type = region_type

    def distribute(self) -> List[List[LocationWithHeight]]:
        locations = self._indoor_cbsd_locations if self._is_indoor else self._outdoor_cbsd_locations
        return CbsdHeightGenerator(
            cbsd_locations=locations,
            region_type=self._region_type,
            distributions=self._distributions).distribute()

    @property
    def _indoor_cbsd_locations(self) -> List[Point]:
        return self._all_cbsd_locations[:self._number_of_indoor_cbsds]

    @property
    def _outdoor_cbsd_locations(self) -> List[Point]:
        return self._all_cbsd_locations[self._number_of_indoor_cbsds:]

    @property
    def _all_cbsd_locations(self) -> List[Point]:
        return [location_with_bearing.coordinates for location_with_bearing in self._cbsd_locations_and_bearings]

    @property
    def _number_of_indoor_cbsds(self) -> int:
        return round(self._number_of_cbsds * self._percentage_of_indoor_aps)

    @property
    def _number_of_cbsds(self) -> int:
        return len(self._cbsd_locations_and_bearings)

    @property
    def _percentage_of_indoor_aps(self) -> float:
        percentage_map = PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE_CATEGORY_A \
            if self._is_category_a else\
            PERCENTAGE_OF_INDOOR_APS_BY_REGION_TYPE_CATEGORY_B
        return percentage_map[self._region_type]

    @property
    def _is_category_a(self) -> bool:
        return self._cbsd_category == CbsdCategories.A

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        return CbsdHeightDistributionsFactory(cbsd_category=self._cbsd_category,
                                              cbsd_type=self._cbsd_type,
                                              is_indoor=self._is_indoor,
                                              region_type=self._region_type).get()
