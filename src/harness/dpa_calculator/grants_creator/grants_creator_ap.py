from typing import Type

from dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import CbsdGetterAp
from dpa_calculator.grants_creator.grants_creator import GrantsCreator


class GrantsCreatorAp(GrantsCreator):
    @property
    def _cbsd_getter(self) -> Type[CbsdGetterAp]:
        return CbsdGetterAp
