from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import CbsdGetterAp

EIRP_AP_INDOOR_CATEGORY_A = 26
EIRP_AP_OUTDOOR_CATEGORY_A = 30


class CbsdGetterApCategoryA(CbsdGetterAp):
    @property
    def _eirp_maximum(self) -> int:
        return EIRP_AP_INDOOR_CATEGORY_A if self._is_indoor else EIRP_AP_OUTDOOR_CATEGORY_A
