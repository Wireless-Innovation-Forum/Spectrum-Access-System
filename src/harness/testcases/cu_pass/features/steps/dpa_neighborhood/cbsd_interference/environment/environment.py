from dataclasses import dataclass
from typing import List

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator import \
    InterferenceComponents
from dpa_calculator.aggregate_interference_monte_carlo_calculator import InterferenceParameters
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa


@dataclass
class ContextCbsdInterference(ContextCbsdCreation, InterferenceParameters, ContextDpa):
    interference_components: List[InterferenceComponents]
