from behave import given

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation, get_current_cbsd_deployment_options


@given("a category {cbsd_category:CbsdCategory} simulation distance of {distance:Integer} km")
def step_impl(context: ContextCbsdCreation, cbsd_category: CbsdCategories, distance: int):
    cbsd_deployment_options = get_current_cbsd_deployment_options(context=context, default=CbsdDeploymentOptions(
        simulation_distances_in_kilometers={}
    ))
    cbsd_deployment_options.simulation_distances_in_kilometers[cbsd_category] = distance
