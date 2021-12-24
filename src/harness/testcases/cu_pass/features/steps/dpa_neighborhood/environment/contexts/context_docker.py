from cu_pass.dpa_calculator.dpa.builder import RadioAstronomyFacilityNames
from testcases.cu_pass.features.environment.hooks import ContextSas
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_monte_carlo_iterations import \
    ContextMonteCarloIterations
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_simulation_area import \
    ContextSimulationArea

ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_DPA_NAME = RadioAstronomyFacilityNames.HatCreek.value
ARBITRARY_NUMBER_OF_ITERATIONS = 1
ARBITRARY_RADIUS_IN_KILOMETERS = 2
ARBITRARY_OBJECT_NAME_LOG = 'arbitrary_object_name_log.log'
ARBITRARY_OBJECT_NAME_RESULT = 'arbitrary_object_name_result.json'


class ContextDocker(ContextSimulationArea, ContextMonteCarloIterations, ContextSas):
    dpa_name: str
    local_filepath_log: str
    local_filepath_result: str
    precreate_bucket: bool
    s3_bucket: str
    s3_object_name_log: str
    s3_object_name_result: str


def set_docker_context_defaults(context: ContextDocker) -> None:
    context.dpa_name = ARBITRARY_DPA_NAME
    context.local_filepath_log = ARBITRARY_OBJECT_NAME_LOG
    context.local_filepath_result = ARBITRARY_OBJECT_NAME_RESULT
    context.precreate_bucket = True
    context.number_of_iterations = ARBITRARY_NUMBER_OF_ITERATIONS
    context.simulation_area_radius = ARBITRARY_RADIUS_IN_KILOMETERS
    context.s3_bucket = ARBITRARY_BUCKET_NAME
    context.s3_object_name_log = ARBITRARY_OBJECT_NAME_LOG
    context.s3_object_name_result = ARBITRARY_OBJECT_NAME_RESULT
