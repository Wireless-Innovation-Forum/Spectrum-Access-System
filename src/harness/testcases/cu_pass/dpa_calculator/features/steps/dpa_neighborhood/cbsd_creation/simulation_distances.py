from behave import given

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_cbsd_deployment_options import \
    get_current_simulation_distances


@given("a category {cbsd_category:CbsdCategory} simulation distance of {distance:Integer} km")
def step_impl(context: ContextCbsdCreation, cbsd_category: CbsdCategories, distance: int):
    simulation_distances = get_current_simulation_distances(context=context, default={})
    simulation_distances[cbsd_category] = distance
