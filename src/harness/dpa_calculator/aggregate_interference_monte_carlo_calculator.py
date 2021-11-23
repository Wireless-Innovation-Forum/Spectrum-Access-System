from dataclasses import dataclass
from pathlib import Path

from dpa_calculator.aggregate_interference_calculator import AggregateInterferenceCalculator
from dpa_calculator.grants_creator import GrantsCreator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import run_monte_carlo_simulation
from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class InterferenceParameters:
    dpa: Dpa
    dpa_test_zone: AreaCircle
    number_of_aps: int


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self, interference_parameters: InterferenceParameters, number_of_iterations: int):
        self._interference_parameters = interference_parameters
        self._number_of_iterations = number_of_iterations

    def simulate(self) -> float:
        return run_monte_carlo_simulation(function_to_run=self._single_run, number_of_iterations=self._number_of_iterations)

    def _single_run(self) -> float:
        grants_creator = GrantsCreator(dpa_zone=self._interference_parameters.dpa_test_zone,
                                       number_of_cbsds=self._interference_parameters.number_of_aps)
        grants = grants_creator.create()
        grants_creator.write_to_kml(Path('grants.kml'))
        return AggregateInterferenceCalculator(dpa=self._interference_parameters.dpa, grants=grants).calculate()
