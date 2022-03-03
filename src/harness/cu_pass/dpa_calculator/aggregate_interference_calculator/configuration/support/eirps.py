from collections import defaultdict
from typing import Dict

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, \
    REGION_TYPE_TYPE, REGION_TYPE_URBAN
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution_uniform import \
    FractionalDistributionUniform

INDOOR_OUTDOOR_TYPE = bool
EIRP_DISTRIBUTION_MAP_TYPE = Dict[CbsdTypes, Dict[CbsdCategories, Dict[REGION_TYPE_TYPE, Dict[INDOOR_OUTDOOR_TYPE, FractionalDistribution]]]]

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

DEFAULT_EIRPS: EIRP_DISTRIBUTION_MAP_TYPE = {
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
    CbsdTypes.UE: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: EIRP_UE)))
}
