import argparse
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import ContextManager, Optional
from uuid import uuid4

import boto3
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator, AggregateInterferenceMonteCarloResults
from cu_pass.dpa_calculator.dpa.builder import get_dpa


DEFAULT_NUMBER_OF_ITERATIONS = 100
DEFAULT_SIMULATION_AREA_IN_KILOMETERS = 100
LOG_EXTENSION = '.log'
LOG_PREFIX = 'log_tmp'
RESULTS_EXTENSION = '.json'
RESULTS_PREFIX = 'results_tmp'


class Main:
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

        self._log_filename = 'log.log'
        self._result_filename = 'result.json'

    def run(self) -> None:
        self._setup_logging_handler()
        self._validate_args()
        with self._setup_output_recording():
            self._calculate()

    def _setup_logging_handler(self) -> None:
        logging.root.addHandler(self._file_handler)

    @contextmanager
    def _setup_output_recording(self) -> ContextManager[None]:
        try:
            yield
        finally:
            self._cleanup_file_handler()
            self._upload_output_log_to_s3()
            self._clean_local_logs()

    def _validate_args(self) -> None:
        self._validate_s3_bucket()

    def _validate_s3_bucket(self) -> None:
        if self._s3_bucket:
            buckets = self._s3_client.list_buckets()['Buckets']
            bucket_names = (bucket['Name'] for bucket in buckets)
            if self._s3_bucket not in bucket_names:
                raise LookupError(f'"{self._s3_bucket}" does not exist.')

    def _calculate(self) -> None:
        dpa = get_dpa(dpa_name=self._dpa_name)
        results = AggregateInterferenceMonteCarloCalculator(
            dpa=dpa,
            number_of_iterations=self._number_of_iterations,
            simulation_area_radius_in_kilometers=self._simulation_area_radius_in_kilometers).simulate()
        results.log()
        self._record_results(results=results)

    def _record_results(self, results: AggregateInterferenceMonteCarloResults) -> None:
        try:
            self._write_local_results(results=results)
            if self._s3_object_result:
                self._upload_file_to_s3(filepath=self._results_filepath, s3_object_name=self._s3_object_result)
        finally:
            self._clean_local_results()

    @property
    def _s3_object_result(self) -> Optional[str]:
        if self._s3_output_directory_with_runtime:
            return self._append_part_to_filepath(self._s3_output_directory_with_runtime, self._result_filename)

    @property
    def _s3_output_directory_with_runtime(self) -> Optional[str]:
        return self._s3_output_directory and self._append_runtime_to_directory(directory=self._s3_output_directory)

    def _write_local_results(self, results: AggregateInterferenceMonteCarloResults) -> None:
        with open(self._results_filepath, 'w') as f:
            f.write(results.to_json())

    def _clean_local_results(self) -> None:
        output_should_persist_locally = self._local_result_filepath
        if not output_should_persist_locally:
            self._results_filepath.unlink()

    @cached_property
    def _results_filepath(self) -> Path:
        return self._get_filepath(self._local_result_filepath or f'{RESULTS_PREFIX}_{uuid4().hex}{RESULTS_EXTENSION}')

    @property
    def _local_result_filepath(self) -> Optional[str]:
        if self._local_output_directory:
            return self._append_part_to_filepath(self._local_output_directory_with_runtime, self._result_filename)

    @property
    def _local_output_directory_with_runtime(self) -> Optional[str]:
        return self._local_output_directory and self._append_runtime_to_directory(directory=self._local_output_directory)

    def _append_runtime_to_directory(self, directory: str) -> str:
        datetime_string = self._runtime.strftime('%Y_%m_%d-%H_%M_%S')
        return self._append_part_to_filepath(directory, datetime_string)

    @cached_property
    def _runtime(self) -> datetime:
        return datetime.now()

    @staticmethod
    def _append_part_to_filepath(filepath: str, new_part: str) -> str:
        return str(Path(filepath, new_part))

    def _cleanup_file_handler(self) -> None:
        self._file_handler.close()
        logging.root.removeHandler(self._file_handler)

    @cached_property
    def _file_handler(self) -> logging.FileHandler:
        file_handler = logging.FileHandler(filename=str(self._output_log_filepath))
        file_handler.setLevel(logging.INFO)
        return file_handler

    def _clean_local_logs(self) -> None:
        output_should_persist_locally = self._local_output_directory
        if not output_should_persist_locally:
            self._output_log_filepath.unlink()

    def _upload_output_log_to_s3(self) -> None:
        if self._s3_object_log:
            self._upload_file_to_s3(filepath=self._output_log_filepath, s3_object_name=self._s3_object_log)

    @property
    def _s3_object_log(self) -> Optional[str]:
        if self._s3_output_directory:
            return self._append_part_to_filepath(filepath=self._s3_output_directory_with_runtime, new_part=self._log_filename)

    def _upload_file_to_s3(self, filepath: Path, s3_object_name: str) -> None:
        self._s3_client.upload_file(str(filepath), self._s3_bucket, s3_object_name)

    @property
    def _s3_client(self):
        return boto3.client('s3')

    @cached_property
    def _output_log_filepath(self) -> Path:
        return self._get_filepath(self._local_log_filepath or f'{LOG_PREFIX}_{uuid4().hex}{LOG_EXTENSION}')

    @property
    def _local_log_filepath(self) -> Optional[str]:
        if self._local_output_directory:
            return self._append_part_to_filepath(self._local_output_directory_with_runtime, self._log_filename)

    @staticmethod
    def _get_filepath(filepath_str: str) -> Path:
        filepath = Path(filepath_str)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        return filepath


def init():
    if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('--dpa-name',
                            dest='dpa_name',
                            type=str,
                            required=True,
                            help='DPA name for which to find neighborhood distance')
        parser.add_argument('--iterations',
                            dest='number_of_iterations',
                            type=int,
                            default=DEFAULT_NUMBER_OF_ITERATIONS,
                            help='The number of Monte Carlo iterations to perform')
        parser.add_argument('--local-output-directory',
                            dest='local_output_directory',
                            type=str,
                            help='The filepath in which a local copy of the logs will be written')
        parser.add_argument('--radius',
                            dest='simulation_area_radius_in_kilometers',
                            type=int,
                            default=DEFAULT_SIMULATION_AREA_IN_KILOMETERS,
                            help='The radius of the simulation area')
        parser.add_argument('--s3-bucket',
                            dest='s3_bucket',
                            type=str,
                            help='S3 Bucket in which to upload output logs')
        parser.add_argument('--s3-output-directory',
                            dest='s3_output_directory',
                            type=str,
                            help='S3 Object in which to upload output logs')
        args = parser.parse_args()

        Main(**args.__dict__).run()


init()
