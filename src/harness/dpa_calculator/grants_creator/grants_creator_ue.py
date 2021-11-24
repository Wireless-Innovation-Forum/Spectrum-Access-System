from typing import Type

from dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ue import CbsdGetterUe
from dpa_calculator.grants_creator.cbsd_height_distributor.cbsd_height_distributor import CbsdHeightDistributorAp, \
    CbsdHeightDistributorUe
from dpa_calculator.grants_creator.cbsd_height_distributor.height_distribution_definitions import \
    OUTDOOR_UE_HEIGHT_IN_METERS
from dpa_calculator.grants_creator.grants_creator import GrantsCreator


class GrantsCreatorUe(GrantsCreator):
    @property
    def _cbsd_height_distributor_class(self) -> Type[CbsdHeightDistributorUe]:
        return CbsdHeightDistributorUe

    @property
    def _outdoor_antenna_height(self) -> float:
        return OUTDOOR_UE_HEIGHT_IN_METERS

    @property
    def _cbsd_getter_class(self) -> Type[CbsdGetterUe]:
        return CbsdGetterUe
