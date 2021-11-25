from dataclasses import dataclass
from pathlib import Path

from dpa_calculator.aggregate_interference_calculator import AggregateInterferenceCalculator
from dpa_calculator.grants_creator.utilities import get_grants_creator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utilities import run_monte_carlo_simulation
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
        interference_access_point = run_monte_carlo_simulation(function_to_run=self._single_run_access_point, number_of_iterations=self._number_of_iterations)
        interference_user_equipment = run_monte_carlo_simulation(function_to_run=self._single_run_user_equipment, number_of_iterations=self._number_of_iterations)
        return max(interference_access_point, interference_user_equipment)

    def _single_run_access_point(self) -> float:
        return self._single_run_cbsd(is_user_equipment=False)

    def _single_run_user_equipment(self) -> float:
        return self._single_run_cbsd(is_user_equipment=True)

    def _single_run_cbsd(self, is_user_equipment: bool) -> float:
        grants_creator = get_grants_creator(dpa_zone=self._interference_parameters.dpa_test_zone,
                                            is_user_equipment=is_user_equipment,
                                            number_of_aps=self._interference_parameters.number_of_aps)
        grants = grants_creator.create()
        grants_creator.write_to_kml(self._kml_output_filepath(is_user_equipment=is_user_equipment))
        return AggregateInterferenceCalculator(dpa=self._interference_parameters.dpa, grants=grants).calculate()

    @staticmethod
    def _kml_output_filepath(is_user_equipment: bool) -> Path:
        return Path(f'grants_{is_user_equipment}.kml')
