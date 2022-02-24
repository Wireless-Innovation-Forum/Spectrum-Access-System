from typing import List

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.dpa.builder import RadioAstronomyFacilityNames
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from testcases.cu_pass.dpa_calculator.features.environment.hooks import ContextSas
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_cbsd_deployment_options import \
    ContextCbsdDeploymentOptions
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_monte_carlo_iterations import \
    ContextMonteCarloIterations
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.parsers.parse_dpa import parse_dpa

ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_DPA_NAME = RadioAstronomyFacilityNames.HatCreek.value
ARBITRARY_NUMBER_OF_ITERATIONS = 1
ARBITRARY_RADIUS_IN_KILOMETERS = 2
ARBITRARY_OUTPUT_DIRECTORY = 'arbitrary_output_directory'


class ContextDocker(ContextCbsdDeploymentOptions, ContextMonteCarloIterations, ContextSas):
    beamwidth: float
    dpa: Dpa
    local_output_directory: str
    include_ue_runs: bool
    interference_threshold: int
    neighborhood_categories: List[CbsdCategories]
    precreate_bucket: bool
    s3_bucket: str
    s3_output_directory: str


def set_docker_context_defaults(context: ContextDocker) -> None:
    context.beamwidth = None
    context.dpa = parse_dpa(text=ARBITRARY_DPA_NAME)
    context.include_ue_runs = False
    context.local_output_directory = ARBITRARY_OUTPUT_DIRECTORY
    context.interference_threshold = None
    context.neighborhood_categories = []
    context.precreate_bucket = True
    context.number_of_iterations = ARBITRARY_NUMBER_OF_ITERATIONS
    context.simulation_area_radius = ARBITRARY_RADIUS_IN_KILOMETERS
    context.s3_bucket = ARBITRARY_BUCKET_NAME
    context.s3_output_directory = ARBITRARY_OUTPUT_DIRECTORY
