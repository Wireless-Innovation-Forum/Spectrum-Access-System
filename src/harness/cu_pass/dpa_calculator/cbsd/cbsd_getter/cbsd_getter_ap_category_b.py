import random

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import CbsdGetterAp
from cu_pass.dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN

EIRP_AP_OUTDOOR_CATEGORY_B_MAXIMUM = 47
EIRP_AP_OUTDOOR_CATEGORY_B_MINIMUM = 40


class CbsdGetterApCategoryB(CbsdGetterAp):
    @property
    def _eirp_maximum(self) -> int:
        return EIRP_AP_OUTDOOR_CATEGORY_B_MAXIMUM \
            if self._dpa_region_type in [REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN] \
            else random.uniform(EIRP_AP_OUTDOOR_CATEGORY_B_MINIMUM, EIRP_AP_OUTDOOR_CATEGORY_B_MAXIMUM)
