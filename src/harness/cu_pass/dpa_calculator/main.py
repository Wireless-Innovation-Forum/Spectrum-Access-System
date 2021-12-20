import argparse
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import ContextManager
from uuid import uuid4

import boto3
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator, AggregateInterferenceMonteCarloResults
from cu_pass.dpa_calculator.dpa.builder import get_dpa


class Main:
    def __init__(self, dpa_name: str, s3_bucket: str, s3_object_log: str, s3_object_result: str):
        self._dpa_name = dpa_name
        self._s3_bucket = s3_bucket
        self._s3_object_log = s3_object_log
        self._s3_object_result = s3_object_result

    def run(self) -> None:
        with self._setup_output_logging():
            self._calculate()

    @contextmanager
    def _setup_output_logging(self) -> ContextManager[None]:
        logging.root.addHandler(self._file_handler)
        try:
            yield
        finally:
            self._cleanup_file_handler()
            self._upload_output_log_to_s3()
            self._clean_local_logs()

    def _cleanup_file_handler(self) -> None:
        self._file_handler.close()
        logging.root.removeHandler(self._file_handler)

    @cached_property
    def _file_handler(self) -> logging.FileHandler:
        file_handler = logging.FileHandler(filename=str(self._output_log_filepath))
        file_handler.setLevel(logging.INFO)
        return file_handler

    def _clean_local_logs(self) -> None:
        self._output_log_filepath.unlink()

    def _calculate(self) -> None:
        dpa = get_dpa(dpa_name=self._dpa_name)
        results = AggregateInterferenceMonteCarloCalculator(dpa=dpa, number_of_iterations=1, simulation_area_radius_in_kilometers=10).simulate()
        results.log()
        self._upload_output_results_to_s3(results=results)

    def _upload_output_log_to_s3(self) -> None:
        self._upload_file_to_s3(filepath=self._output_log_filepath, s3_object_name=self._s3_object_log)

    def _upload_output_results_to_s3(self, results: AggregateInterferenceMonteCarloResults) -> None:
        results_filepath = Path('results_tmp.json')
        try:
            with open(results_filepath, 'w') as f:
                f.write(results.to_json())
            self._upload_file_to_s3(filepath=results_filepath, s3_object_name=self._s3_object_result)
        finally:
            results_filepath.unlink()

    def _upload_file_to_s3(self, filepath: Path, s3_object_name: str) -> None:
        s3_client = boto3.client('s3')
        s3_client.create_bucket(Bucket=self._s3_bucket)
        s3_client.upload_file(str(filepath), self._s3_bucket, s3_object_name)

    @cached_property
    def _output_log_filepath(self) -> Path:
        return Path(f'output_log_filename_{uuid4().hex}.log')


def init():
    if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('--dpa-name', dest='dpa_name', type=str, help='DPA name for which to find neighborhood distance')
        parser.add_argument('--s3-bucket', dest='s3_bucket', type=str, help='S3 Bucket in which to upload output logs')
        parser.add_argument('--s3-object-log', dest='s3_object_log', type=str, help='S3 Object in which to upload output logs')
        parser.add_argument('--s3-object-result', dest='s3_object_result', type=str, help='S3 Object in which to upload output results')
        args = parser.parse_args()

        Main(**args.__dict__).run()


init()
