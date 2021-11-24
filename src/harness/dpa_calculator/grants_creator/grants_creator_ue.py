from typing import Type

from dpa_calculator.cbsd import CbsdGetterUe
from dpa_calculator.grants_creator.grants_creator import GrantsCreator


class GrantsCreatorUe(GrantsCreator):
    @property
    def _cbsd_getter(self) -> Type[CbsdGetterUe]:
        return CbsdGetterUe
