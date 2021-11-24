from typing import Type

from dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import CbsdGetterAp
from dpa_calculator.grants_creator.cbsd_height_distributor.cbsd_height_distributor import CbsdHeightDistributorAp
from dpa_calculator.grants_creator.cbsd_height_distributor.height_distribution_definitions import \
    OUTDOOR_AP_HEIGHT_IN_METERS
from dpa_calculator.grants_creator.grants_creator import GrantsCreator


class GrantsCreatorAp(GrantsCreator):
    @property
    def _cbsd_height_distributor_class(self) -> Type[CbsdHeightDistributorAp]:
        return CbsdHeightDistributorAp

    @property
    def _outdoor_antenna_height(self) -> float:
        return OUTDOOR_AP_HEIGHT_IN_METERS

    @property
    def _cbsd_getter_class(self) -> Type[CbsdGetterAp]:
        return CbsdGetterAp
