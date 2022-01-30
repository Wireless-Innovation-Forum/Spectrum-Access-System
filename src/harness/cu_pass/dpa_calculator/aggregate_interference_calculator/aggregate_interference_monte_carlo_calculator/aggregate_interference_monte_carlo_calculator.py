import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import auto, Enum
from json import JSONEncoder
from math import inf
from typing import Any, Type

import numpy
import numpy as np

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum import \
    AggregateInterferenceCalculatorWinnforum
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.cbsd_deployer import \
    CbsdDeployer
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from cu_pass.dpa_calculator.binary_search.parameter_finder import ParameterFinder
from cu_pass.dpa_calculator.binary_search.binary_search import InputWithReturnedValue
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger, get_dpa_center, run_monte_carlo_simulation
from reference_models.dpa.move_list import PROTECTION_PERCENTILE

DEFAULT_MONTE_CARLO_ITERATIONS = 1000
NEIGHBORHOOD_STEP_SIZE_DEFAULT = 16
THRESHOLD_MARGIN = 1


class AggregateInterferenceTypes(Enum):
    NTIA = auto()
    WinnForum = auto()


DEFAULT_AGGREGATE_INTERFERENCE_TYPE = AggregateInterferenceTypes.WinnForum


class RuntimeEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, timedelta):
            return str(o)
        else:
            super().default(o=o)


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
        logger = get_dpa_calculator_logger()
        logger.info(f'\nFinal results:')
        logger.info(f'\tDistance: {self.distance}')
        logger.info(f'\tInterference: {self.interference}')
        logger.info(f'\tRuntime: {self.runtime}')
        logger.info(f'\tAP Distance: {self.distance_access_point}')
        logger.info(f'\tUE Distance: {self.distance_user_equipment}')
        logger.info(f'\tAP Interference: {self.interference_access_point}')
        logger.info(f'\tUE Interference: {self.interference_user_equipment}')
        logger.info(f'\tRuntime: {self.runtime}')

    def to_json(self) -> str:
        dictionary = asdict(self)
        return json.dumps(dictionary, cls=RuntimeEncoder)


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self,
                 dpa: Dpa,
                 number_of_iterations: int = DEFAULT_MONTE_CARLO_ITERATIONS,
                 aggregate_interference_calculator_type: AggregateInterferenceTypes = DEFAULT_AGGREGATE_INTERFERENCE_TYPE,
                 cbsd_deployment_options: CbsdDeploymentOptions = CbsdDeploymentOptions()):
        self._aggregate_interference_calculator_type = aggregate_interference_calculator_type
        self._cbsd_deployment_options = cbsd_deployment_options
        self._dpa = dpa
        self._number_of_iterations = number_of_iterations

        self._found_interferences = {
            CbsdTypes.AP: defaultdict(list),
            CbsdTypes.UE: defaultdict(list)
        }

    def simulate(self) -> AggregateInterferenceMonteCarloResults:
        self._log_inputs()
        start_time = datetime.now()
        distances = run_monte_carlo_simulation(
            functions_to_run=[self._single_run_access_point, self._single_run_user_equipment],
            number_of_iterations=self._number_of_iterations,
            percentile=PROTECTION_PERCENTILE)
        [distance_access_point, distance_user_equipment] = distances
        expected_interference_access_point,\
            expected_interference_user_equipment = (self._get_interference_at_distance(distance=cbsd_type_distance,
                                                                                       cbsd_type=cbsd_type)
                                                    for cbsd_type_distance, cbsd_type in zip(distances, CbsdTypes))
        distance = max(distances)
        expected_interference = expected_interference_user_equipment if distance == distance_user_equipment else expected_interference_access_point
        return AggregateInterferenceMonteCarloResults(
            distance=int(distance),
            distance_access_point=int(distance_access_point),
            distance_user_equipment=int(distance_user_equipment),
            interference=float(expected_interference),
            interference_access_point=float(expected_interference_access_point),
            interference_user_equipment=float(expected_interference_user_equipment),
            runtime=datetime.now() - start_time
        )

    def _log_inputs(self) -> None:
        logger = get_dpa_calculator_logger()
        logger.info('Inputs:')
        logger.info(f'\tDPA Name: {self._dpa.name}')
        logger.info(f'\tNumber of iterations: {self._number_of_iterations}')
        logger.info(f'\tAggregate interference calculator: {self._aggregate_interference_calculator_class.__name__}')
        logger.info('')

    def _get_interference_at_distance(self, distance: int, cbsd_type: CbsdTypes) -> float:
        percentile = numpy.percentile(self._found_interferences[cbsd_type][distance], PROTECTION_PERCENTILE)
        return -inf if np.isnan(percentile) else percentile

    def _single_run_access_point(self) -> float:
        result = self._single_run_cbsd(is_user_equipment=False)
        return result.input

    def _single_run_user_equipment(self) -> float:
        result = self._single_run_cbsd(is_user_equipment=True)
        return result.input

    def _single_run_cbsd(self, is_user_equipment: bool) -> InputWithReturnedValue:
        interference_calculator = self._aggregate_interference_calculator(is_user_equipment=is_user_equipment)
        result = ParameterFinder(
            function=interference_calculator.calculate,
            target=self._dpa.threshold - THRESHOLD_MARGIN,
            max_parameter=self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.B],
            step_size=NEIGHBORHOOD_STEP_SIZE_DEFAULT,
        ).find()
        result.log()
        self._track_interference_from_distance(cbsd_type=CbsdTypes.UE if is_user_equipment else CbsdTypes.AP,
                                               found_result=result)
        return result

    def _aggregate_interference_calculator(self, is_user_equipment: bool) -> AggregateInterferenceCalculator:
        cbsds_with_bearings = self._random_cbsds_with_bearings(is_user_equipment=is_user_equipment)
        return self._aggregate_interference_calculator_class(dpa=self._dpa, cbsds_with_bearings=cbsds_with_bearings)

    def _random_cbsds_with_bearings(self, is_user_equipment: bool) -> CbsdsWithBearings:
        cbsd_deployer = self._cbsd_deployer_category(is_user_equipment=is_user_equipment)
        cbsd_deployer.log()
        return cbsd_deployer.deploy()

    def _cbsd_deployer_category(self, is_user_equipment) -> CbsdDeployer:
        return CbsdDeployer(center=get_dpa_center(dpa=self._dpa),
                            is_user_equipment=is_user_equipment,
                            cbsd_deployment_options=self._cbsd_deployment_options)

    @property
    def _aggregate_interference_calculator_class(self) -> Type[AggregateInterferenceCalculator]:
        map = {
            AggregateInterferenceTypes.NTIA: AggregateInterferenceCalculatorNtia,
            AggregateInterferenceTypes.WinnForum: AggregateInterferenceCalculatorWinnforum
        }
        return map[self._aggregate_interference_calculator_type]

    def _track_interference_from_distance(self, cbsd_type: CbsdTypes, found_result: InputWithReturnedValue) -> None:
        self._found_interferences[cbsd_type][found_result.input].append(found_result.returned_value)
