from typing import Type

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import CbsdGetterAp
from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap_category_a import CbsdGetterApCategoryA
from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap_category_b import CbsdGetterApCategoryB
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_distributor import \
    CbsdHeightDistributorAccessPointCategoryA, CbsdHeightDistributorAccessPointCategoryB
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsCreator


class CbsdsCreatorAccessPoint(CbsdsCreator):
    @property
    def _cbsd_height_distributor_class(self) -> Type[CbsdHeightDistributorAccessPointCategoryA]:
        return CbsdHeightDistributorAccessPointCategoryA \
            if self._is_category_a \
            else CbsdHeightDistributorAccessPointCategoryB

    @property
    def _cbsd_getter_class(self) -> Type[CbsdGetterAp]:
        return CbsdGetterApCategoryA if self._is_category_a else CbsdGetterApCategoryB
