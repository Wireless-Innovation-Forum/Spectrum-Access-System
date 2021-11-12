from dataclasses import dataclass

from behave import *
from behave import runner

from dpa_calculator.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.point_distributor import AreaCircle, PointDistributor
from dpa_calculator.utils import Point
from reference_models.dpa.dpa_mgr import Dpa


@dataclass
class ContextMonteCarlo(runner.Context):
    dpa: Dpa
    exclusion_zone_distance: int



@given("an antenna at {dpa:Dpa}")
def step_impl(context: ContextMonteCarlo, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa = dpa


@step("an exclusion zone distance of {distance:Integer} km")
def step_impl(context: ContextMonteCarlo, distance: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.exclusion_zone_distance = distance


@when("a monte carlo simulation of {number_of_iterations:Integer} iterations of the aggregate interference is run")
def step_impl(context: ContextMonteCarlo, number_of_iterations: int):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_aps = NumberOfApsCalculatorGroundBased(simulation_population=6384440).get_number_of_aps()
    for trial in range(number_of_iterations):
        distribution_area = AreaCircle(
            center_coordinates=Point.from_shapely(point_shapely=context.dpa.geometry.centroid),
            radius_in_kilometers=context.exclusion_zone_distance
        )
        ap_distribution = PointDistributor(distribution_area=distribution_area).distribute_points(number_of_points=number_of_aps)


@then("the probability of exceeding -144 INR is 95%")
def step_impl(context: ContextMonteCarlo):
    """
    Args:
        context (behave.runner.Context):
    """
    raise NotImplementedError(u'STEP: Then the propagation loss is high enough to make the interference negligible')
