from behave import given

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    SIMULATION_DISTANCES_DEFAULT
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_simulation_distances import \
    ContextSimulationDistances


@given("a category {cbsd_category:CbsdCategory} simulation distance of {distance:Integer} km")
def step_impl(context: ContextSimulationDistances, cbsd_category: CbsdCategories, distance: int):
    if not hasattr(context, 'simulation_distances'):
        context.simulation_distances = SIMULATION_DISTANCES_DEFAULT
    context.simulation_distances[cbsd_category] = distance
