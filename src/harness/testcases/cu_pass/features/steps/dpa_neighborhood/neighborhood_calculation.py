import random
from dataclasses import dataclass
from functools import partial

from behave import *
from behave.api.async_step import async_run_until_complete

from dpa_calculator.aggregate_interference_monte_carlo_calculator import AggregateInterferenceMonteCarloCalculator, \
    InterferenceParameters
from dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from dpa_calculator.parameter_finder import ParameterFinder
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.population_retriever.population_retriever_straight_file import PopulationRetrieverStraightFile
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.result import ContextResult

use_step_matcher('parse')


@dataclass
class ContextNeighborhood(ContextResult, ContextDpa):
    interference_to_noise_ratio: int


@step("an INR of {interference_to_noise_ratio:Integer}")
def step_impl(context: ContextNeighborhood, interference_to_noise_ratio: int):
    """
    Args:
        context (behave.runner.Context):
    """
    context.interference_to_noise_ratio = interference_to_noise_ratio


@when("the neighborhood radius is calculated")
@async_run_until_complete
async def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    async def perform_test():
        await main_test(context=context)

    if context.with_integration:
        await perform_test()
    else:
        await perform_test()
        # arbitrary_population = 5000
        # with mock_worldpop(returned_population=arbitrary_population):
        #     await perform_test()


async def main_test(context: ContextNeighborhood):
    random.seed(0)
    func_part = partial(function, context=context)
    interference_threshold = context.interference_to_noise_ratio
    context.result = await ParameterFinder(function=func_part, target=interference_threshold).find()


async def function(neighborhood_radius: int, context: ContextNeighborhood) -> float:
    default_iterations = 1
    area = AreaCircle(
        center_coordinates=Point.from_shapely(point_shapely=context.dpa.geometry.centroid),
        radius_in_kilometers=neighborhood_radius
    )
    population = await PopulationRetrieverStraightFile(area=area).retrieve()
    number_of_aps = NumberOfApsCalculatorGroundBased(simulation_population=population).get_number_of_aps()
    parameters = InterferenceParameters(
        dpa=context.dpa,
        dpa_test_zone=area,
        number_of_aps=number_of_aps
    )
    return AggregateInterferenceMonteCarloCalculator(interference_parameters=parameters,
                                                     number_of_iterations=default_iterations).simulate()
