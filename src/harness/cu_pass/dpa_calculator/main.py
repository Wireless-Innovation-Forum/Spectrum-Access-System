import argparse
import logging
from pathlib import Path
from uuid import uuid4

import boto3
from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator
from cu_pass.dpa_calculator.dpa.builder import get_dpa


class Main:
    def __init__(self, s3_bucket: str, s3_object: str):
        self._s3_bucket = s3_bucket
        self._s3_object = s3_object

    def run(self) -> None:
        self._calculate()
        self._upload_output_log_to_s3()
        self._clean_local_logs()

    def _clean_local_logs(self) -> None:
        Path(self._output_log_filename).unlink()

    def _calculate(self) -> None:
        with open(self._output_log_filename, 'w') as f:
            f.write('content')

        # logging.basicConfig(level=logging.INFO)
        #
        # dpa = get_dpa(dpa_name='Hat Creek')
        # results = AggregateInterferenceMonteCarloCalculator(dpa=dpa, number_of_iterations=2, simulation_area_radius_in_kilometers=100).simulate()

    def _upload_output_log_to_s3(self) -> None:
        s3_client = boto3.client('s3')
        s3_client.create_bucket(Bucket=self._s3_bucket)
        s3_client.upload_file(self._output_log_filename, self._s3_bucket, self._s3_object)

    @cached_property
    def _output_log_filename(self) -> str:
        return f'output_log_filename_{uuid4().hex}'


def init():
    if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('--s3-bucket', dest='s3_bucket', type=str, help='S3 Bucket in which to upload output logs')
        parser.add_argument('--s3-object', dest='s3_object', type=str, help='S3 Object in which to upload output logs')
        args = parser.parse_args()

        Main(s3_bucket=args.s3_bucket, s3_object=args.s3_object).run()


init()
