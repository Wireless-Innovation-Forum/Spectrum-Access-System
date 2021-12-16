from dataclasses import dataclass
from typing import Type

from behave import *

from behave.api.async_step import async_run_until_complete

from cu_pass.dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from cu_pass.dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.area import ContextArea

use_step_matcher('parse')


@dataclass
class ContextPopulation(ContextArea):
    retriever: Type[PopulationRetriever]


@given("{retriever_type} population data")
def step_impl(context: ContextPopulation, retriever_type: str):
    if retriever_type == 'census':
        context.retriever = PopulationRetrieverCensus


@then("the population in the area should be {expected_population:Integer}")
@async_run_until_complete
async def step_impl(context: ContextPopulation, expected_population: int):
    """
    Args:
        context (behave.runner.Context):
    """
    population = context.retriever(area=context.area).retrieve()
    assert population == expected_population, f'{population} != {expected_population}'
