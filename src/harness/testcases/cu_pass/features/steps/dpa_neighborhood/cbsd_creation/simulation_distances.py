from behave import given

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_simulation_distances import \
    ContextSimulationDistances


@given("a category {cbsd_category:CbsdCategory} simulation distance of {distance:Integer} km")
def step_impl(context: ContextSimulationDistances, cbsd_category: CbsdCategories, distance: int):
    if not hasattr(context, 'simulation_distances'):
        context.simulation_distances = {}
    context.simulation_distances[cbsd_category] = distance
