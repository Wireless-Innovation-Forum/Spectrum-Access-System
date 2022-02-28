import random
from abc import ABC
from collections import defaultdict
from typing import Dict

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, \
    REGION_TYPE_TYPE, \
    REGION_TYPE_URBAN
from cu_pass.dpa_calculator.helpers.list_distributor import FractionalDistribution, FractionalDistributionUniform
from cu_pass.dpa_calculator.utilities import Point

EIRP_AP_INDOOR_CATEGORY_A = FractionalDistributionUniform(fraction=1,
                                                          range_maximum=26,
                                                          range_minimum=26)
EIRP_AP_OUTDOOR_CATEGORY_A = FractionalDistributionUniform(fraction=1,
                                                           range_maximum=30,
                                                           range_minimum=30)

EIRP_AP_OUTDOOR_CATEGORY_B_URBAN = FractionalDistributionUniform(fraction=1,
                                                                 range_maximum=47,
                                                                 range_minimum=40)

EIRP_AP_OUTDOOR_CATEGORY_B_NOT_URBAN = FractionalDistributionUniform(fraction=1,
                                                                     range_maximum=47,
                                                                     range_minimum=47)

EIRP_UE = FractionalDistributionUniform(fraction=1,
                                        range_maximum=24,
                                        range_minimum=24)

GAIN_AP = 6
GAIN_UE = 0

INDOOR_OUTDOOR_TYPE = bool

DEFAULT_EIRPS: Dict[CbsdTypes, Dict[CbsdCategories, Dict[REGION_TYPE_TYPE, Dict[INDOOR_OUTDOOR_TYPE, FractionalDistribution]]]] = {
    CbsdTypes.AP: {
        CbsdCategories.A: defaultdict(lambda: {
                True: EIRP_AP_INDOOR_CATEGORY_A,
                False: EIRP_AP_OUTDOOR_CATEGORY_A
        }),
        CbsdCategories.B: {
            REGION_TYPE_DENSE_URBAN: {False: EIRP_AP_OUTDOOR_CATEGORY_B_URBAN},
            REGION_TYPE_RURAL: {False: EIRP_AP_OUTDOOR_CATEGORY_B_NOT_URBAN},
            REGION_TYPE_SUBURBAN: {False: EIRP_AP_OUTDOOR_CATEGORY_B_NOT_URBAN},
            REGION_TYPE_URBAN: {False: EIRP_AP_OUTDOOR_CATEGORY_B_URBAN},
        }
    },
    CbsdTypes.UE: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: EIRP_UE))))
}


class CbsdVariability:
    eirp: int
    gain: int


class CbsdGetter(ABC):
    def __init__(self,
                 category: CbsdCategories,
                 cbsd_type: CbsdTypes,
                 dpa_region_type: str,
                 height: float,
                 is_indoor: bool,
                 location: Point):
        self._category = category
        self._cbsd_type = cbsd_type
        self._dpa_region_type = dpa_region_type
        self._height = height
        self._is_indoor = is_indoor
        self._location = location

    def get(self) -> Cbsd:
        return Cbsd(cbsd_category=self._category,
                    cbsd_type=self._cbsd_type,
                    eirp_maximum=self._eirp_maximum,
                    gain=self._gain,
                    height_in_meters=self._height,
                    is_indoor=self._is_indoor,
                    location=self._location)

    @property
    def _eirp_maximum(self) -> float:
        distribution = DEFAULT_EIRPS[self._cbsd_type][self._category][self._dpa_region_type][self._is_indoor]
        return distribution.get_values(number_of_values=1)[0]

    @property
    def _gain(self) -> int:
        if self._is_user_equipment:
            return GAIN_UE
        else:
            return GAIN_AP

    @property
    def _is_category_a(self) -> bool:
        return self._category == CbsdCategories.A

    @property
    def _is_user_equipment(self) -> bool:
        return self._cbsd_type == CbsdTypes.UE
