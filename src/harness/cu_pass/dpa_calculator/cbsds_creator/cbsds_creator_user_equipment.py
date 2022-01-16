from typing import Type

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ue import CbsdGetterUe
from cu_pass.dpa_calculator.cbsds_creator.cbsd_height_distributor.cbsd_height_distributor import \
    CbsdHeightDistributorUserEquipment
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsCreator


class CbsdsCreatorUserEquipment(CbsdsCreator):
    @property
    def _cbsd_height_distributor_class(self) -> Type[CbsdHeightDistributorUserEquipment]:
        return CbsdHeightDistributorUserEquipment

    @property
    def _cbsd_getter_class(self) -> Type[CbsdGetterUe]:
        return CbsdGetterUe
