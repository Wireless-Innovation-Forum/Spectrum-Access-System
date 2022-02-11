from abc import ABC

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdTypes
from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdGetter

GAIN_AP = 6


class CbsdGetterAp(CbsdGetter, ABC):
    @property
    def _cbsd_type(self) -> CbsdTypes:
        return CbsdTypes.AP

    @property
    def _gain(self) -> int:
        return GAIN_AP
