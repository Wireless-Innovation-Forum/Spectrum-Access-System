from behave import given

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.cbsd_deployer import \
    NEIGHBORHOOD_DISTANCES_DEFAULT, NEIGHBORHOOD_DISTANCES_TYPE
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.environment.hooks import ContextSas


class ContextSimulationDistances(ContextSas):
    simulation_distances: NEIGHBORHOOD_DISTANCES_TYPE


@given("a category {cbsd_category:CbsdCategory} simulation distance of {distance:Integer} km")
def step_impl(context: ContextSimulationDistances, cbsd_category: CbsdCategories, distance: int):
    if not hasattr(context, 'neighborhood_distances'):
        context.simulation_distances = NEIGHBORHOOD_DISTANCES_DEFAULT
    context.simulation_distances[cbsd_category] = distance
