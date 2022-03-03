from typing import Dict, List

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.height_distribution_definitions import \
    HeightDistribution, INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A, INDOOR_UE_HEIGHT_DISTRIBUTION, \
    OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_B, OUTDOOR_UE_HEIGHT_DISTRIBUTION
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution


class CbsdHeightDistributionsFactory:
    def __init__(self, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes, is_indoor: bool, region_type: str):
        self._cbsd_type = cbsd_type
        self._cbsd_category = cbsd_category
        self._is_indoor = is_indoor
        self._region_type = region_type

    def get(self) -> List[FractionalDistribution]:
        return self._distributions

    @property
    def _distributions(self) -> List[FractionalDistribution]:
        height_distributions = self._height_distribution_map[self._region_type]
        return [distribution.to_fractional_distribution() for distribution in height_distributions]

    @property
    def _height_distribution_map(self) -> Dict[str, List[HeightDistribution]]:
        return self._distribution_ue if self._is_ue else self._distribution_ap

    @property
    def _is_ue(self) -> bool:
        return self._cbsd_type == CbsdTypes.UE

    @property
    def _distribution_ue(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_UE_HEIGHT_DISTRIBUTION \
            if self._is_indoor \
            else OUTDOOR_UE_HEIGHT_DISTRIBUTION

    @property
    def _distribution_ap(self) -> Dict[str, List[HeightDistribution]]:
        return INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A \
            if self._is_category_a \
            else OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_B

    @property
    def _is_category_a(self) -> bool:
        return self._cbsd_category == CbsdCategories.A
