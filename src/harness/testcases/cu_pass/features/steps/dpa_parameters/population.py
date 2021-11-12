from dataclasses import dataclass

from behave import *

from behave.api.async_step import async_run_until_complete

from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from testcases.cu_pass.features.steps.dpa_parameters.area import ContextArea


@dataclass
class ContextPopulation(ContextArea):
    pass


@then("the population in the area should be {expected_population:Number}")
@async_run_until_complete
async def step_impl(context: ContextPopulation, expected_population: float):
    """
    Args:
        context (behave.runner.Context):
    """
    population = await PopulationRetriever(area=context.area).retrieve()
    assert population == expected_population, f'{population} != {expected_population}'
