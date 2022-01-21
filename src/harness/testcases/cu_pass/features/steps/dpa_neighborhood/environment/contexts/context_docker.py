from cu_pass.dpa_calculator.dpa.builder import RadioAstronomyFacilityNames
from testcases.cu_pass.features.environment.hooks import ContextSas
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_monte_carlo_iterations import \
    ContextMonteCarloIterations

ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_DPA_NAME = RadioAstronomyFacilityNames.HatCreek.value
ARBITRARY_NUMBER_OF_ITERATIONS = 1
ARBITRARY_RADIUS_IN_KILOMETERS = 2
ARBITRARY_OUTPUT_DIRECTORY = 'arbitrary_output_directory'


class ContextDocker(ContextMonteCarloIterations, ContextSas):
    dpa_name: str
    local_output_directory: str
    precreate_bucket: bool
    s3_bucket: str
    s3_output_directory: str


def set_docker_context_defaults(context: ContextDocker) -> None:
    context.dpa_name = ARBITRARY_DPA_NAME
    context.local_output_directory = ARBITRARY_OUTPUT_DIRECTORY
    context.precreate_bucket = True
    context.number_of_iterations = ARBITRARY_NUMBER_OF_ITERATIONS
    context.simulation_area_radius = ARBITRARY_RADIUS_IN_KILOMETERS
    context.s3_bucket = ARBITRARY_BUCKET_NAME
    context.s3_output_directory = ARBITRARY_OUTPUT_DIRECTORY
