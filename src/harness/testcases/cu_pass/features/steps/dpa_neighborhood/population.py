from dataclasses import dataclass

from behave import *

from behave.api.async_step import async_run_until_complete

from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from testcases.cu_pass.features.steps.dpa_neighborhood.area import ContextArea
from testcases.cu_pass.features.steps.dpa_neighborhood.helpers.mock_worldpop import mock_worldpop


@dataclass
class ContextPopulation(ContextArea):
    pass


@then("the population in the area should be {expected_population:Integer}")
@async_run_until_complete
async def step_impl(context: ContextPopulation, expected_population: int):
    """
    Args:
        context (behave.runner.Context):
    """
    async def perform_test():
        await main_test(context=context, expected_population=expected_population)

    if context.with_integration:
        await perform_test()
    else:
        with mock_worldpop(returned_population=expected_population):
            await perform_test()


async def main_test(context: ContextPopulation, expected_population: int):
    population = await PopulationRetriever(area=context.area).retrieve()
    assert population == expected_population, f'{population} != {expected_population}'
