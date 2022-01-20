from contextlib import contextmanager
from typing import ContextManager, Optional

import boto3
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator, AggregateInterferenceMonteCarloResults
from cu_pass.dpa_calculator.dpa.builder import get_dpa
from cu_pass.dpa_calculator.main_runner.results_recorder import ResultsRecorder

DEFAULT_NUMBER_OF_ITERATIONS = 100
DEFAULT_SIMULATION_AREA_IN_KILOMETERS = 100


class MainRunner:
    def __init__(self,
                 dpa_name: str,
                 number_of_iterations: int = DEFAULT_NUMBER_OF_ITERATIONS,
                 simulation_area_radius_in_kilometers: int = DEFAULT_SIMULATION_AREA_IN_KILOMETERS,
                 local_output_directory: Optional[str] = None,
                 s3_bucket: Optional[str] = None,
                 s3_output_directory: Optional[str] = None):
        self._dpa_name = dpa_name
        self._local_output_directory = local_output_directory
        self._number_of_iterations = number_of_iterations
        self._simulation_area_radius_in_kilometers = simulation_area_radius_in_kilometers
        self._s3_bucket = s3_bucket
        self._s3_output_directory = s3_output_directory

    def run(self) -> None:
        self._setup_logging_handler()
        self._validate_args()
        with self._setup_output_recording():
            results = self._calculate()
            results.log()
            self._record_results(results=results)

    def _setup_logging_handler(self) -> None:
        self._results_recorder.setup_logging_handler()

    def _validate_args(self) -> None:
        self._validate_s3_bucket()

    def _validate_s3_bucket(self) -> None:
        if self._s3_bucket:
            buckets = self._s3_client.list_buckets()['Buckets']
            bucket_names = (bucket['Name'] for bucket in buckets)
            if self._s3_bucket not in bucket_names:
                raise LookupError(f'"{self._s3_bucket}" does not exist.')

    @contextmanager
    def _setup_output_recording(self) -> ContextManager[None]:
        with self._results_recorder.prepare_for_recording():
            yield

    def _calculate(self) -> AggregateInterferenceMonteCarloResults:
        dpa = get_dpa(dpa_name=self._dpa_name)
        return AggregateInterferenceMonteCarloCalculator(
            dpa=dpa,
            number_of_iterations=self._number_of_iterations,
            simulation_area_radius_in_kilometers=self._simulation_area_radius_in_kilometers).simulate()

    def _record_results(self, results: AggregateInterferenceMonteCarloResults) -> None:
        self._results_recorder.record(results=results)

    @cached_property
    def _results_recorder(self) -> ResultsRecorder:
        return ResultsRecorder(local_output_directory=self._local_output_directory,
                               s3_bucket=self._s3_bucket,
                               s3_output_directory=self._s3_output_directory)

    @property
    def _s3_client(self):
        return boto3.client('s3')
