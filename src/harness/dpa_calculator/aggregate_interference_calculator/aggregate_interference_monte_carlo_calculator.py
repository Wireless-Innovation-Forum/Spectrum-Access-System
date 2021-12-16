import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import auto, Enum
from typing import Optional, Type

import numpy
from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum import \
    AggregateInterferenceCalculatorWinnforum
from dpa_calculator.cbsd.cbsd import CbsdTypes
from dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from dpa_calculator.cbsds_creator.utilities import get_cbsds_creator
from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsCalculator
from dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from dpa_calculator.parameter_finder import InputWithReturnedValue, ParameterFinder
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from dpa_calculator.utilities import get_dpa_center, run_monte_carlo_simulation
from reference_models.dpa.move_list import PROTECTION_PERCENTILE

DEFAULT_MONTE_CARLO_ITERATIONS = 1000
DEFAULT_SIMULATION_RADIUS_IN_KILOMETERS = 500


class AggregateInterferenceTypes(Enum):
    NTIA = auto()
    WinnForum = auto()


@dataclass
class InterferenceParameters:
    dpa: Dpa
    number_of_aps: int


@dataclass
class AggregateInterferenceMonteCarloResults:
    distance: int
    distance_access_point: float
    distance_user_equipment: float
    interference: float
    interference_access_point: float
    interference_user_equipment: float
    runtime: timedelta

    def log(self) -> None:
        logging.info(f'\nFinal results:')
        logging.info(f'\tDistance: {self.distance}')
        logging.info(f'\tInterference: {self.interference}')
        logging.info(f'\tRuntime: {self.runtime}')
        logging.info(f'\tAP Distance: {self.distance_access_point}')
        logging.info(f'\tUE Distance: {self.distance_user_equipment}')
        logging.info(f'\tAP Interference: {self.interference_access_point}')
        logging.info(f'\tUE Interference: {self.interference_user_equipment}')
        logging.info(f'\tRuntime: {self.runtime}')


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self,
                 dpa: Dpa,
                 number_of_iterations: int = DEFAULT_MONTE_CARLO_ITERATIONS,
                 number_of_aps: Optional[int] = None,
                 simulation_area_radius_in_kilometers: int = DEFAULT_SIMULATION_RADIUS_IN_KILOMETERS,
                 aggregate_interference_calculator_type: AggregateInterferenceTypes = AggregateInterferenceTypes.NTIA,
                 population_retriever_class: Type[PopulationRetriever] = PopulationRetrieverCensus,
                 number_of_aps_calculator_class: Type[NumberOfApsCalculator] = NumberOfApsCalculatorShipborne):
        self._dpa = dpa
        self._number_of_aps_override = number_of_aps
        self._number_of_iterations = number_of_iterations
        self._simulation_area_radius_in_kilometers = simulation_area_radius_in_kilometers
        self._aggregate_interference_calculator_type = aggregate_interference_calculator_type
        self._population_retriever_class = population_retriever_class
        self._number_of_aps_calculator_class = number_of_aps_calculator_class

        self._found_interferences = {
            CbsdTypes.AP: defaultdict(list),
            CbsdTypes.UE: defaultdict(list)
        }

    def simulate(self) -> AggregateInterferenceMonteCarloResults:
        start_time = datetime.now()
        [distance_access_point, distance_user_equipment] = run_monte_carlo_simulation(
            functions_to_run=[self._single_run_access_point, self._single_run_user_equipment],
            number_of_iterations=self._number_of_iterations,
            percentile=PROTECTION_PERCENTILE)
        distance = max(distance_access_point, distance_user_equipment)
        expected_interference_access_point, expected_interference_user_equipment = (numpy.percentile(self._found_interferences[cbsd_type][distance], PROTECTION_PERCENTILE)
                                                                                    for cbsd_type in CbsdTypes)
        expected_interference = expected_interference_user_equipment if distance == distance_user_equipment else expected_interference_access_point
        return AggregateInterferenceMonteCarloResults(
            distance=distance,
            distance_access_point=distance_access_point,
            distance_user_equipment=distance_user_equipment,
            interference=expected_interference,
            interference_access_point=expected_interference_access_point,
            interference_user_equipment=expected_interference_user_equipment,
            runtime=datetime.now() - start_time
        )

    def _single_run_access_point(self) -> float:
        result = self._single_run_cbsd(is_user_equipment=False)
        self._track_interference_from_distance(cbsd_type=CbsdTypes.AP, found_result=result)
        return result.input

    def _single_run_user_equipment(self) -> float:
        result = self._single_run_cbsd(is_user_equipment=True)
        self._track_interference_from_distance(cbsd_type=CbsdTypes.UE, found_result=result)
        return result.input

    def _single_run_cbsd(self, is_user_equipment: bool) -> InputWithReturnedValue:
        interference_calculator = self._aggregate_interference_calculator(is_user_equipment=is_user_equipment)
        result = ParameterFinder(function=interference_calculator.calculate,
                                 target=self._dpa.threshold,
                                 max_parameter=self._simulation_area_radius_in_kilometers).find()
        result.log()
        return result

    def _aggregate_interference_calculator(self, is_user_equipment: bool) -> AggregateInterferenceCalculator:
        cbsds_with_bearings = self._random_cbsds_with_bearings(is_user_equipment=is_user_equipment)
        return self._aggregate_interference_calculator_class(dpa=self._dpa, cbsds_with_bearings=cbsds_with_bearings)

    @property
    def _aggregate_interference_calculator_class(self) -> Type[AggregateInterferenceCalculator]:
        map = {
            AggregateInterferenceTypes.NTIA: AggregateInterferenceCalculatorNtia,
            AggregateInterferenceTypes.WinnForum: AggregateInterferenceCalculatorWinnforum
        }
        return map[self._aggregate_interference_calculator_type]

    def _random_cbsds_with_bearings(self, is_user_equipment: bool) -> CbsdsWithBearings:
        cbsds_creator = get_cbsds_creator(dpa_zone=self._dpa_test_zone,
                                          is_user_equipment=is_user_equipment,
                                          number_of_aps=self._number_of_aps)
        cbsds = cbsds_creator.create()
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
            radius_in_kilometers=self._simulation_area_radius_in_kilometers
        )

    def _track_interference_from_distance(self, cbsd_type: CbsdTypes, found_result: InputWithReturnedValue) -> None:
        self._found_interferences[cbsd_type][found_result.input].append(found_result.returned_value)

