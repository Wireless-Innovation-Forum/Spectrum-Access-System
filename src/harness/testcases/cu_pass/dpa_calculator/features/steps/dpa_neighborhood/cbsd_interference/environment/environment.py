from dataclasses import dataclass
from typing import List

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from cu_pass.dpa_calculator.aggregate_interference_calculator.configuration.support.eirps import \
    EIRP_AP_OUTDOOR_CATEGORY_A
from reference_models.dpa.dpa_mgr import Dpa
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa

ARBITRARY_ANTENNA_HEIGHT_IN_METERS = 3
ARBITRARY_EIRP_MAXIMUM = EIRP_AP_OUTDOOR_CATEGORY_A


@dataclass
class ContextCbsdInterference(ContextCbsdCreation, ContextDpa):
    dpa: Dpa
    interference_components: List[InterferenceComponents]
    number_of_aps: int
