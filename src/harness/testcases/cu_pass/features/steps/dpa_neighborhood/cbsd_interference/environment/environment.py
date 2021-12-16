from dataclasses import dataclass
from typing import List

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import InterferenceParameters
from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter_ap import EIRP_AP_OUTDOOR
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa

ARBITRARY_ANTENNA_HEIGHT_IN_METERS = 3
ARBITRARY_EIRP_MAXIMUM = EIRP_AP_OUTDOOR


@dataclass
class ContextCbsdInterference(ContextCbsdCreation, InterferenceParameters, ContextDpa):
    interference_components: List[InterferenceComponents]
