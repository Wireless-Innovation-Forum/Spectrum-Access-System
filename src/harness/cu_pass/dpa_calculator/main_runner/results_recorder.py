import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloResults
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger

LOG_EXTENSION = '.log'
LOG_PREFIX = 'log_tmp'
RESULTS_EXTENSION = '.json'
RESULTS_PREFIX = 'results_tmp'


class ResultsRecorder:
    def __init__(self,
                 local_output_directory: str,
                 s3_bucket: str,
                 s3_output_directory: str):
        self._local_output_directory = local_output_directory and Path(local_output_directory)
        self._s3_bucket = s3_bucket
        self._s3_output_directory = s3_output_directory and Path(s3_output_directory)

        self._log_filename = 'log.log'
        self._result_filename = 'result.json'

        self._runtime = datetime.now()

    def setup_logging_handler(self) -> None:
        self._logger.addHandler(self._file_handler)

    @contextmanager
    def prepare_for_recording(self) -> None:
        try:
            yield
        finally:
            self._cleanup_file_handler()
            self._upload_output_log_to_s3()
            self._clean_local_logs()

    def _cleanup_file_handler(self) -> None:
        self._file_handler.close()
        self._logger.removeHandler(self._file_handler)

    @cached_property
    def _file_handler(self) -> logging.FileHandler:
        file_handler = logging.FileHandler(filename=str(self._output_log_filepath))
        file_handler.setLevel(logging.INFO)
        self._logger.setLevel(logging.INFO)
        return file_handler

    @property
    def _logger(self) -> logging.Logger:
        return get_dpa_calculator_logger()

    def _upload_output_log_to_s3(self) -> None:
        if self._s3_object_log:
            self._upload_file_to_s3(filepath=self._output_log_filepath, s3_object_name=self._s3_object_log)

    @property
    def _s3_object_log(self) -> Optional[str]:
        if self._s3_output_directory:
            filepath = self._append_part_to_filepath(filepath=self._s3_output_directory_with_runtime,
                                                     new_part=self._log_filename)
            return filepath.as_posix()

    @cached_property
    def _output_log_filepath(self) -> Path:
        return self._get_filepath(self._local_log_filepath or f'{LOG_PREFIX}_{uuid4().hex}{LOG_EXTENSION}')

    @property
    def _local_log_filepath(self) -> Optional[str]:
        if self._local_output_directory:
            filepath = self._append_part_to_filepath(self._local_output_directory_with_runtime, self._log_filename)
            return str(filepath.absolute())

    def _clean_local_logs(self) -> None:
        output_should_persist_locally = self._local_output_directory
        if not output_should_persist_locally:
            self._output_log_filepath.unlink()

    def record(self, results: AggregateInterferenceMonteCarloResults,) -> None:
        try:
            self._write_local_results(results=results)
            if self._s3_object_result:
                self._upload_file_to_s3(filepath=self._results_filepath, s3_object_name=self._s3_object_result)
        finally:
            self._clean_local_results()

    def _write_local_results(self, results: AggregateInterferenceMonteCarloResults,) -> None:
        with open(self._results_filepath, 'w') as f:
            f.write(results.to_json())

    @cached_property
    def _results_filepath(self) -> Path:
        return self._get_filepath(
            self._local_result_filepath or f'{RESULTS_PREFIX}_{uuid4().hex}{RESULTS_EXTENSION}')

    @staticmethod
    def _get_filepath(filepath_str: str) -> Path:
        filepath = Path(filepath_str)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        return filepath

    @property
    def _s3_object_result(self) -> Optional[str]:
        if self._s3_output_directory_with_runtime:
            filepath = self._append_part_to_filepath(self._s3_output_directory_with_runtime, self._result_filename)
            return filepath.as_posix()

    @property
    def _s3_output_directory_with_runtime(self) -> Optional[Path]:
        return self._s3_output_directory and self._append_runtime_to_directory(directory=self._s3_output_directory)

    def _upload_file_to_s3(self, filepath: Path, s3_object_name: str) -> None:
        self._s3_client.upload_file(str(filepath), self._s3_bucket, s3_object_name)

    @property
    def _s3_client(self):
        return boto3.client('s3')

    def _clean_local_results(self) -> None:
        output_should_persist_locally = self._local_result_filepath
        if not output_should_persist_locally:
            self._results_filepath.unlink()

    @property
    def _local_result_filepath(self) -> Optional[str]:
        if self._local_output_directory:
            filepath = self._append_part_to_filepath(self._local_output_directory_with_runtime, self._result_filename)
            return str(filepath.absolute())

    @property
    def _local_output_directory_with_runtime(self) -> Optional[Path]:
        return self._local_output_directory and self._append_runtime_to_directory(directory=self._local_output_directory)

    def _append_runtime_to_directory(self, directory: Path) -> Path:
        datetime_string = self._runtime.strftime('%Y_%m_%d-%H_%M_%S')
        return self._append_part_to_filepath(directory, datetime_string)

    @staticmethod
    def _append_part_to_filepath(filepath: Path, new_part: str) -> Path:
        return Path(filepath, new_part)
