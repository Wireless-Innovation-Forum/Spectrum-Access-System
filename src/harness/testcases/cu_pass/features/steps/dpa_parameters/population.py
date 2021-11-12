from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager
from unittest import mock
from unittest.mock import Mock

from behave import *

from behave.api.async_step import async_run_until_complete
from worldpop_client.api import services_api, tasks_api
from worldpop_client.model.stats_response import StatsResponse
from worldpop_client.model.tasks_response import TasksResponse

from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from testcases.cu_pass.features.steps.dpa_parameters.area import ContextArea

ARBITRARY_TASK_ID = 'arbitrary_task_id'


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
        with with_mocks(expected_population=expected_population):
            await perform_test()


async def main_test(context: ContextPopulation, expected_population: int):
    population = await PopulationRetriever(area=context.area).retrieve()
    assert population == expected_population, f'{population} != {expected_population}'


@contextmanager
def with_mocks(expected_population: int) -> ContextManager[None]:
    with mock_stats_get() as stats_get_mock:
        with mock_tasks_get(expected_population=expected_population) as task_get_mock:
            yield
            stats_get_mock.assert_called_once()
            task_get_mock.assert_called_once_with(task_id=ARBITRARY_TASK_ID)


@contextmanager
def mock_stats_get() -> ContextManager[Mock]:
    with mock.patch.object(services_api.ServicesApi, 'services_stats_get') as stats_get_mock:
        stats_get_mock.return_value = StatsResponse(
            status='created',
            status_code=200,
            error=False,
            taskid=ARBITRARY_TASK_ID
        )
        yield stats_get_mock


@contextmanager
def mock_tasks_get(expected_population: int) -> ContextManager[Mock]:
    with mock.patch.object(tasks_api.TasksApi, 'tasks_task_id_get') as task_get_mock:
        task_get_mock.return_value = TasksResponse(
            status='finished',
            status_code=200,
            error=False,
            data={
                'total_population': expected_population
            }
        )
        yield task_get_mock
