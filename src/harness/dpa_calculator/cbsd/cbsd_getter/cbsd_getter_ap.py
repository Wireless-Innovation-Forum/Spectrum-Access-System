from dpa_calculator.cbsd.cbsd import CbsdTypes
from dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdGetter

EIRP_AP_INDOOR = 26
EIRP_AP_OUTDOOR = 30
GAIN_AP = 6


class CbsdGetterAp(CbsdGetter):
    @property
    def _cbsd_type(self) -> CbsdTypes:
        return CbsdTypes.AP

    @property
    def _gain(self) -> int:
        return GAIN_AP

    @property
    def _eirp_maximum(self) -> int:
        return EIRP_AP_INDOOR if self._is_indoor else EIRP_AP_OUTDOOR
