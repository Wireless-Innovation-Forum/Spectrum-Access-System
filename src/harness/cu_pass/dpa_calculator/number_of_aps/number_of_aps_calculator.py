from abc import abstractmethod
from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Dict, Optional

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes

from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, \
    REGION_TYPE_URBAN
from cu_pass.dpa_calculator.utilities import Point


FRACTION_OF_USERS_REGION_TYPE_DICT = Dict[CbsdCategories, Dict[str, float]]
NUMBER_OF_CBSDS_REGION_TYPE_DICT = Dict[CbsdCategories, Dict[str, int]]
NUMBER_OF_CBSDS_FOR_POPULATION_TYPE = Dict[CbsdCategories, int]
NUMBER_OF_CBSDS_TYPE = Dict[CbsdTypes, int]
NUMBER_OF_CBSDS_PER_CATEGORY_TYPE = Dict[CbsdCategories, NUMBER_OF_CBSDS_TYPE]

FRACTION_OF_USERS_SERVED_BY_APS_DEFAULT: FRACTION_OF_USERS_REGION_TYPE_DICT = {
    CbsdCategories.A: {
        REGION_TYPE_DENSE_URBAN: .8,
        REGION_TYPE_RURAL: .4,
        REGION_TYPE_SUBURBAN: .6,
        REGION_TYPE_URBAN: .8
    },
    CbsdCategories.B: {
        REGION_TYPE_DENSE_URBAN: .2,
        REGION_TYPE_RURAL: .6,
        REGION_TYPE_SUBURBAN: .4,
        REGION_TYPE_URBAN: .2
    }
}

NUMBER_OF_UES_PER_AP_BY_REGION_TYPE_DEFAULT: NUMBER_OF_CBSDS_REGION_TYPE_DICT = {
    CbsdCategories.A: {
        REGION_TYPE_DENSE_URBAN: 50,
        REGION_TYPE_RURAL: 3,
        REGION_TYPE_SUBURBAN: 20,
        REGION_TYPE_URBAN: 50
    },
    CbsdCategories.B: {
        REGION_TYPE_DENSE_URBAN: 200,
        REGION_TYPE_RURAL: 500,
        REGION_TYPE_SUBURBAN: 200,
        REGION_TYPE_URBAN: 200
    }
}


class NumberOfApsTypes(Enum):
    ground_based = auto()
    shipborne = auto()


@dataclass
class NumberOfCbsdsCalculatorOptions:
    fraction_of_users_served_by_aps: FRACTION_OF_USERS_REGION_TYPE_DICT = field(default_factory=lambda: FRACTION_OF_USERS_SERVED_BY_APS_DEFAULT)
    number_of_ues_per_ap_by_region_type: NUMBER_OF_CBSDS_REGION_TYPE_DICT = field(default_factory=lambda: NUMBER_OF_UES_PER_AP_BY_REGION_TYPE_DEFAULT)
    number_of_cbsds_calculator_type: NumberOfApsTypes = NumberOfApsTypes.shipborne


class NumberOfCbsdsCalculator:
    def __init__(self, center_coordinates: Point, simulation_population: int,
                 number_of_cbsds_calculator_options: Optional[NumberOfCbsdsCalculatorOptions] = NumberOfCbsdsCalculatorOptions()):
        self._fraction_of_users_served_by_aps = number_of_cbsds_calculator_options.fraction_of_users_served_by_aps
        self._number_of_ues_per_ap_by_region_type = number_of_cbsds_calculator_options.number_of_ues_per_ap_by_region_type
        self._center_coordinates = center_coordinates
        self._simulation_population = simulation_population

    @abstractmethod
    def get_number_of_cbsds(self) -> NUMBER_OF_CBSDS_PER_CATEGORY_TYPE:
        raise NotImplementedError
