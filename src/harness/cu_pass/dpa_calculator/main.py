import argparse

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    SIMULATION_DISTANCES_DEFAULT
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.main_runner.main_runner import DEFAULT_NUMBER_OF_ITERATIONS, MainRunner


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
        parser.add_argument('--category-a-radius',
                            dest='simulation_distance_category_a',
                            type=int,
                            default=SIMULATION_DISTANCES_DEFAULT[CbsdCategories.A],
                            help='The radius of the simulation area')
        parser.add_argument('--category-b-radius',
                            dest='simulation_distance_category_b',
                            type=int,
                            default=SIMULATION_DISTANCES_DEFAULT[CbsdCategories.B],
                            help='The radius of the simulation area')
        parser.add_argument('--s3-bucket',
                            dest='s3_bucket',
                            type=str,
                            help='S3 Bucket in which to upload output logs')
        parser.add_argument('--s3-output-directory',
                            dest='s3_output_directory',
                            type=str,
                            help='S3 Object in which to upload output logs')
        parser.add_argument('--include-ue-runs',
                            dest='include_ue_runs',
                            action='store_true',
                            help='Run UE simulations in addition to AP simulations')
        parser.add_argument('--neighborhood-category',
                            dest='neighborhood_category',
                            type=str,
                            help='Set a specific neighborhood distance to calculate. Options include "A" or "B". '
                                 'If not specified, both will be calculated.')
        parser.add_argument('--interference-threshold',
                            dest='interference_threshold',
                            type=int,
                            help='Sets the interference threshold for the DPA. '
                                 'If unspecified, current definitions for the DPA will be used.')
        parser.add_argument('--beamwidth',
                            dest='beamwidth',
                            type=float,
                            help='Sets the beamwidth of the DPA antenna.')
        parser.add_argument('--eirp-a',
                            dest='eirp_category_a',
                            type=str,
                            help='Sets EIRP distribution for category A APs.'
                                 'Uniform example: "50%: 20-26, 50%: 26-30"'
                                 'Normal example: "100%: PDF [5-26] mean 14 std 3"')
        parser.add_argument('--eirp-b',
                            dest='eirp_category_b',
                            type=str,
                            help='Sets EIRP distribution for category B APs.'
                                 'Uniform example: "50%: 20-26, 50%: 26-30"'
                                 'Normal example: "100%: PDF [5-26] mean 14 std 3"')
        args = parser.parse_args()

        MainRunner(**args.__dict__).run()


init()
