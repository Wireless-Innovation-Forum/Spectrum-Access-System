from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Type

from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsds_creator.utilities import get_cbsds_creator
from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsCalculator
from dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from dpa_calculator.parameter_finder import ParameterFinder
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from dpa_calculator.utilities import get_dpa_center, run_monte_carlo_simulation
from reference_models.dpa.move_list import PROTECTION_PERCENTILE

DEFAULT_MONTE_CARLO_ITERATIONS = 1000
DEFAULT_SIMULATION_RADIUS = 200


@dataclass
class InterferenceParameters:
    dpa: Dpa
    number_of_aps: int


@dataclass
class AggregateInterferenceMonteCarloResults:
    distance: float
    distance_access_point: float
    distance_user_equipment: float
    runtime: timedelta


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self,
                 dpa: Dpa,
                 target_threshold: float,
                 number_of_iterations: int = DEFAULT_MONTE_CARLO_ITERATIONS,
                 number_of_aps: Optional[int] = None,
                 aggregate_interference_calculator_class: Type[AggregateInterferenceCalculator] = AggregateInterferenceCalculatorNtia,
                 population_retriever_class: Type[PopulationRetriever] = PopulationRetrieverCensus,
                 number_of_aps_calculator_class: Type[NumberOfApsCalculator] = NumberOfApsCalculatorShipborne):
        self._dpa = dpa
        self._number_of_aps_override = number_of_aps
        self._number_of_iterations = number_of_iterations
        self._target_threshold = target_threshold
        self._aggregate_interference_calculator_class = aggregate_interference_calculator_class
        self._population_retriever_class = population_retriever_class
        self._number_of_aps_calculator_class = number_of_aps_calculator_class

    def simulate(self) -> AggregateInterferenceMonteCarloResults:
        start_time = datetime.now()
        [interference_access_point, interference_user_equipment] = run_monte_carlo_simulation(
            functions_to_run=[self._single_run_access_point, self._single_run_user_equipment],
            number_of_iterations=self._number_of_iterations,
            percentile=PROTECTION_PERCENTILE)
        return AggregateInterferenceMonteCarloResults(
            distance=max(interference_access_point, interference_user_equipment),
            distance_access_point=interference_access_point,
            distance_user_equipment=interference_user_equipment,
            runtime=datetime.now() - start_time
        )

    def _single_run_access_point(self) -> float:
        return self._single_run_cbsd(is_user_equipment=False)

    def _single_run_user_equipment(self) -> float:
        return self._single_run_cbsd(is_user_equipment=True)

    def _single_run_cbsd(self, is_user_equipment: bool) -> float:
        interference_calculator = self._aggregate_interference_calculator(is_user_equipment=is_user_equipment)
        return ParameterFinder(function=interference_calculator.calculate, target=self._target_threshold).find()

    def _aggregate_interference_calculator(self, is_user_equipment: bool) -> AggregateInterferenceCalculator:
        cbsds = self._random_cbsds(is_user_equipment=is_user_equipment)
        return self._aggregate_interference_calculator_class(dpa=self._dpa, cbsds=cbsds)

    def _random_cbsds(self, is_user_equipment: bool) -> List[Cbsd]:
        cbsds_creator = get_cbsds_creator(dpa_zone=self._dpa_test_zone,
                                          is_user_equipment=is_user_equipment,
                                          number_of_aps=self._number_of_aps)
        cbsds = cbsds_creator.create()
        cbsds_creator.write_to_kml(self._kml_output_filepath(is_user_equipment=is_user_equipment))
        return cbsds

    @cached_property
    def _number_of_aps(self) -> int:
        if self._number_of_aps_override:
            return self._number_of_aps_override
        population = self._population_retriever_class(area=self._dpa_test_zone).retrieve()
        return self._number_of_aps_calculator_class(center_coordinates=self._dpa_test_zone.center_coordinates,
                                                    simulation_population=population).get_number_of_aps()

    @property
    def _dpa_test_zone(self) -> AreaCircle:
        return AreaCircle(
            center_coordinates=get_dpa_center(dpa=self._dpa),
            radius_in_kilometers=DEFAULT_SIMULATION_RADIUS
        )

    @staticmethod
    def _kml_output_filepath(is_user_equipment: bool) -> Path:
        return Path(f'grants_{is_user_equipment}.kml')
