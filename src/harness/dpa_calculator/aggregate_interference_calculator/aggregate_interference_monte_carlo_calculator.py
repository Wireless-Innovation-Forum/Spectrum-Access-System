from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.cbsds_creator.utilities import get_cbsds_creator
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utilities import run_monte_carlo_simulation
from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class InterferenceParameters:
    dpa: Dpa
    dpa_test_zone: AreaCircle
    number_of_aps: int


@dataclass
class AggregateInterferenceMonteCarloResults:
    interference_max: float
    interference_access_point: float
    interference_user_equipment: float
    runtime: timedelta


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self, interference_parameters: InterferenceParameters, number_of_iterations: int):
        self._interference_parameters = interference_parameters
        self._number_of_iterations = number_of_iterations

    def simulate(self) -> AggregateInterferenceMonteCarloResults:
        start_time = datetime.now()
        interference_access_point = run_monte_carlo_simulation(function_to_run=self._single_run_access_point, number_of_iterations=self._number_of_iterations)
        interference_user_equipment = run_monte_carlo_simulation(function_to_run=self._single_run_user_equipment, number_of_iterations=self._number_of_iterations)
        return AggregateInterferenceMonteCarloResults(
            interference_max=max(interference_access_point, interference_user_equipment),
            interference_access_point=interference_access_point,
            interference_user_equipment=interference_user_equipment,
            runtime=datetime.now() - start_time
        )

    def _single_run_access_point(self) -> float:
        return self._single_run_cbsd(is_user_equipment=False)

    def _single_run_user_equipment(self) -> float:
        return self._single_run_cbsd(is_user_equipment=True)

    def _single_run_cbsd(self, is_user_equipment: bool) -> float:
        cbsds_creator = get_cbsds_creator(dpa_zone=self._interference_parameters.dpa_test_zone,
                                          is_user_equipment=is_user_equipment,
                                          number_of_aps=self._interference_parameters.number_of_aps)
        cbsds = cbsds_creator.create()
        cbsds_creator.write_to_kml(self._kml_output_filepath(is_user_equipment=is_user_equipment))
        return AggregateInterferenceCalculatorNtia(dpa=self._interference_parameters.dpa, cbsds=cbsds).calculate()

    @staticmethod
    def _kml_output_filepath(is_user_equipment: bool) -> Path:
        return Path(f'grants_{is_user_equipment}.kml')
