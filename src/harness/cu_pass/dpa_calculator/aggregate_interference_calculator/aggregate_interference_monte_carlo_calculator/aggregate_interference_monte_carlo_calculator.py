import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta
from enum import auto, Enum
from functools import partial
from json import JSONEncoder
from math import inf
from typing import Any, Callable, Dict, List, Type

import numpy
import numpy as np
from numpy import int32

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.aggregate_interference_calculator_ntia import \
    AggregateInterferenceCalculatorNtia
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_winnforum.aggregate_interference_calculator_winnforum import \
    AggregateInterferenceCalculatorWinnforum
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.cbsd_deployer import \
    CbsdDeployer
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.binary_search.shortest_unchanging import ShortestUnchangingInputFinder
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from cu_pass.dpa_calculator.binary_search.binary_search import InputWithReturnedValue

from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger, get_dpa_center, get_percentile, \
    run_monte_carlo_simulation
from reference_models.dpa.move_list import PROTECTION_PERCENTILE

DEFAULT_MONTE_CARLO_ITERATIONS = 1000
NEIGHBORHOOD_STEP_SIZE_DEFAULT = 16


class AggregateInterferenceTypes(Enum):
    NTIA = auto()
    WinnForum = auto()


DEFAULT_AGGREGATE_INTERFERENCE_TYPE = AggregateInterferenceTypes.WinnForum
SINGLE_RUN_TYPE = Dict[CbsdCategories, List[InputWithReturnedValue]]
RESULTS_CACHE = Dict[CbsdTypes, SINGLE_RUN_TYPE]


class ResultsEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, timedelta):
            return str(o)
        elif isinstance(o, int32):
            return int(o)
        else:
            super().default(o=o)


@dataclass
class AggregateInterferenceMonteCarloResults:
    distance: Dict[CbsdTypes, Dict[CbsdCategories, int]] = field(default_factory=dict)
    interference: Dict[CbsdTypes, Dict[CbsdCategories, float]] = field(default_factory=dict)
    runtime: timedelta = None

    def log(self) -> None:
        logger = get_dpa_calculator_logger()
        logger.info(f'\nFinal results:')
        logger.info(f'\tRuntime: {self.runtime}')
        logger.info(f'\tDistance: {self.distance}')
        logger.info(f'\tInterference: {self.interference}')
        logger.info(f'\tRuntime: {self.runtime}')

    def to_json(self) -> str:
        dictionary = self._convert_keys_to_string(asdict(self))
        return json.dumps(dictionary, cls=ResultsEncoder)

    def _convert_keys_to_string(self, dictionary: dict):
        if not isinstance(dictionary, dict):
            return dictionary
        return {str(key): self._convert_keys_to_string(value) for key, value in dictionary.items()}


class AggregateInterferenceMonteCarloCalculator:
    def __init__(self,
                 dpa: Dpa,
                 number_of_iterations: int = DEFAULT_MONTE_CARLO_ITERATIONS,
                 aggregate_interference_calculator_type: AggregateInterferenceTypes = DEFAULT_AGGREGATE_INTERFERENCE_TYPE,
                 cbsd_deployment_options: CbsdDeploymentOptions = CbsdDeploymentOptions(),
                 include_ue_runs: bool = False):
        self._aggregate_interference_calculator_type = aggregate_interference_calculator_type
        self._cbsd_deployment_options = cbsd_deployment_options
        self._dpa = dpa
        self._include_ue_runs = include_ue_runs
        self._number_of_iterations = number_of_iterations

        self._found_interferences = {
            CbsdTypes.AP: {
                CbsdCategories.A: defaultdict(list),
                CbsdCategories.B: defaultdict(list)
            },
            CbsdTypes.UE: {
                CbsdCategories.A: defaultdict(list),
                CbsdCategories.B: defaultdict(list)
            }
        }

        self._cached_results: RESULTS_CACHE = defaultdict(lambda: defaultdict(list))

        self._final_result = AggregateInterferenceMonteCarloResults()

    def simulate(self) -> AggregateInterferenceMonteCarloResults:
        self._log_inputs()
        start_time = datetime.now()
        self._run_cbsd_category(CbsdTypes.AP)
        if self._include_ue_runs:
            self._run_cbsd_category(CbsdTypes.UE)
        self._final_result = replace(self._final_result, runtime=datetime.now() - start_time)
        return self._final_result

    def _run_cbsd_category(self, cbsd_type: CbsdTypes) -> None:
        for iteration_number in range(self._number_of_iterations):
            logger = get_dpa_calculator_logger()
            logger.info(f'{cbsd_type} iteration {iteration_number + 1}')
            self._single_run_cbsd(cbsd_type=cbsd_type)
        results_both_categories = {cbsd_category: self._cached_results[cbsd_type][cbsd_category]
                                   for cbsd_category in CbsdCategories}
        distances = {cbsd_category: get_percentile(results=[result.input for result in results],
                                                   percentile=PROTECTION_PERCENTILE)
                     for cbsd_category, results in results_both_categories.items()}
        interferences = {cbsd_category: self._get_interference_at_distance(distance=distance, cbsd_category=cbsd_category, cbsd_type=cbsd_type)
                         for cbsd_category, distance in distances.items()}
        self._final_result.distance[cbsd_type] = distances
        self._final_result.interference[cbsd_type] = interferences

    def _log_inputs(self) -> None:
        self._logger.info('Inputs:')
        self._logger.info(f'\tDPA Name: {self._dpa.name}')
        self._logger.info(f'\tNumber of iterations: {self._number_of_iterations}')
        self._logger.info(
            f'\tAggregate interference calculator: {self._aggregate_interference_calculator_class.__name__}')
        self._logger.info('')

    def _get_interference_at_distance(self, distance: int, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes) -> float:
        percentile = numpy.percentile(self._found_interferences[cbsd_type][cbsd_category][distance], PROTECTION_PERCENTILE)
        return -inf if np.isnan(percentile) else percentile

    @property
    def _functions_to_run(self) -> List[Callable[[], float]]:
        def _read_cached_results(cbsd_category: CbsdCategories, cbsd_type: CbsdTypes):
            return self._cached_results[cbsd_type][cbsd_category][-1].input
        functions = [partial(self._single_run_cbsd, cbsd_category=CbsdCategories.A, cbsd_type=CbsdTypes.AP),
                     partial(_read_cached_results, cbsd_category=CbsdCategories.B, cbsd_type=CbsdTypes.AP)]
        if self._include_ue_runs:
            functions += [partial(self._single_run_cbsd, cbsd_category=CbsdCategories.A, cbsd_type=CbsdTypes.UE),
                          partial(_read_cached_results, cbsd_category=CbsdCategories.B, cbsd_type=CbsdTypes.UE)]
        return functions

    def _single_run_cbsd(self, cbsd_type: CbsdTypes) -> None:
        is_user_equipment = cbsd_type == CbsdTypes.UE
        interference_calculator = self._aggregate_interference_calculator(is_user_equipment=is_user_equipment)
        for cbsd_category_for_cache in CbsdCategories:
            calculate_function = partial(interference_calculator.calculate, cbsd_category=cbsd_category_for_cache)
            result = ShortestUnchangingInputFinder(
                function=calculate_function,
                max_parameter=self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.B],
                step_size=NEIGHBORHOOD_STEP_SIZE_DEFAULT,
            ).find()
            self._logger.info(f'\t{cbsd_category_for_cache} NEIGHBORHOOD RESULTS:')
            result.log()
            self._cached_results[cbsd_type][cbsd_category_for_cache].append(result)
            self._track_interference_from_distance(cbsd_category=cbsd_category_for_cache,
                                                   cbsd_type=cbsd_type,
                                                   found_result=result,
                                                   interference_calculator=interference_calculator)

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

    def _track_interference_from_distance(self,
                                          cbsd_category: CbsdCategories,
                                          cbsd_type: CbsdTypes,
                                          found_result: InputWithReturnedValue,
                                          interference_calculator: AggregateInterferenceCalculator) -> None:
        found_distance = found_result.input
        expected_interference = interference_calculator.get_expected_interference(cbsd_category=cbsd_category,
                                                                                  distance=found_distance)
        self._found_interferences[cbsd_type][cbsd_category][found_distance].append(expected_interference)

        self._log_expected_interference(expected_interference=expected_interference)

    def _log_expected_interference(self, expected_interference: float):
        self._logger.info(f'\t\tExpected Interference: {expected_interference}')
        self._logger.info('')

    @property
    def _logger(self) -> logging.Logger:
        return get_dpa_calculator_logger()
