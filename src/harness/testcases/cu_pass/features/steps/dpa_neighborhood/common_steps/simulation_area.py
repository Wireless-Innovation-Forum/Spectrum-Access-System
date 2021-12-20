from behave import *

from testcases.cu_pass.features.environment.hooks import ContextSas


class ContextSimulationArea(ContextSas):
    simulation_area_radius: int


@given("a simulation area radius of {simulation_area_radius:Integer}")
def step_impl(context: ContextSimulationArea, simulation_area_radius: int):
    context.simulation_area_radius = simulation_area_radius
