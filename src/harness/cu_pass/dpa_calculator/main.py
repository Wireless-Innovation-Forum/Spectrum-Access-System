import argparse

from cu_pass.dpa_calculator.main_runner.main_runner import DEFAULT_NUMBER_OF_ITERATIONS, \
    DEFAULT_SIMULATION_AREA_IN_KILOMETERS, MainRunner


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

        MainRunner(**args.__dict__).run()


init()
