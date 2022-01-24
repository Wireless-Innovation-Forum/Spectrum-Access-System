from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Dict, Optional

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_CBSDS_PER_CATEGORY_TYPE

NEIGHBORHOOD_DISTANCES_TYPE = Dict[CbsdCategories, int]
SIMULATION_DISTANCES_DEFAULT: NEIGHBORHOOD_DISTANCES_TYPE = {CbsdCategories.A: 250, CbsdCategories.B: 500}


class NumberOfApsTypes(Enum):
    ground_based = auto()
    shipborne = auto()


class PopulationRetrieverTypes(Enum):
    census = auto()
    region_type = auto()


@dataclass
class CbsdDeploymentOptions:
    population_override: Optional[int] = None
    simulation_distances_in_kilometers: NEIGHBORHOOD_DISTANCES_TYPE = field(
        default_factory=lambda: SIMULATION_DISTANCES_DEFAULT)
    population_retriever_type: PopulationRetrieverTypes = PopulationRetrieverTypes.census
    number_of_aps_calculator_type: NumberOfApsTypes = NumberOfApsTypes.shipborne
