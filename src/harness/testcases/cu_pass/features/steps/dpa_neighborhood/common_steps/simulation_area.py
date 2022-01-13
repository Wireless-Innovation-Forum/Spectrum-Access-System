from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_simulation_area import \
    ContextSimulationArea


@given("a simulation area radius of {simulation_area_radius:Integer}")
def step_impl(context: ContextSimulationArea, simulation_area_radius: int):
    context.simulation_area_radius = simulation_area_radius
