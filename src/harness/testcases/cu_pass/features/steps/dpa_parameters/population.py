import json
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import ContextManager, Iterable, Union

from behave import *

import worldpop_client
from behave.api.async_step import async_run_until_complete
from urllib3 import poolmanager
from urllib3.util import Url, parse_url
from worldpop_client.api import services_api, tasks_api
from worldpop_client.model.geo_json import GeoJson
from worldpop_client.model.stats_response import StatsResponse
from worldpop_client.model.tasks_response import TasksResponse

from dpa_calculator.circle_to_geojson_converter import CircleToGeoJsonConverter
from dpa_calculator.point_distributor import AreaCircle
from testcases.cu_pass.features.steps.dpa_parameters.area import ContextArea


@dataclass
class ContextPopulation(ContextArea):
    pass


class WorldPopCommunicator:
    @property
    @contextmanager
    def _worldpop_api_client(self) -> ContextManager[worldpop_client.ApiClient]:
        with worldpop_client.ApiClient() as api_client:
            yield api_client

    @property
    @contextmanager
    @abstractmethod
    def _api(self) -> Union[services_api.ServicesApi, tasks_api.TasksApi]:
        raise NotImplementedError


class TaskCreator(WorldPopCommunicator):
    _dataset = 'wpgppop'
    _year = 2020

    def __init__(self, area: AreaCircle):
        self._area = area

    def create(self) -> str:
        with self._api as api_instance:
            api_response: StatsResponse = api_instance.services_stats_get(dataset=self._dataset,
                                                                          year=self._year,
                                                                          geojson=self._geojson_string)
            return api_response.taskid

    @property
    @contextmanager
    def _api(self) -> services_api.ServicesApi:
        with self._worldpop_api_client as api_client:
            yield services_api.ServicesApi(api_client)

    @property
    def _geojson_string(self) -> str:
        return json.dumps(self._geojson.to_dict())

    @property
    def _geojson(self) -> GeoJson:
        return CircleToGeoJsonConverter(area=self._area).convert()


class TaskResultsRetriever(WorldPopCommunicator):
    def __init__(self, task_id: str):
        self._task_id = task_id

    async def retrieve(self) -> TasksResponse:
        for _ in self._try_before_timeout():
            response = self._ping()
            if response.status == 'finished':
                if response.error_message:
                    raise Exception(response.error_message)
                return response

    def _try_before_timeout(self) -> Iterable[None]:
        timeout = datetime.now() + timedelta(minutes=2)
        while datetime.now() < timeout:
            yield
        raise TimeoutError(f'Timeout waiting for task {self._task_id}')

    def _ping(self) -> TasksResponse:
        with self._api as api_instance:
            return api_instance.tasks_task_id_get(task_id=self._task_id)

    @property
    @contextmanager
    def _api(self) -> tasks_api.TasksApi:
        with self._worldpop_api_client as api_client:
            yield tasks_api.TasksApi(api_client)


class PopulationRetriever:
    def __init__(self, area: AreaCircle):
        self._area = area

    async def retrieve(self) -> float:
        task_id = self._create_task()
        return await self._retrieve_population(task_id=task_id)

    def _create_task(self) -> str:
        return TaskCreator(area=self._area).create()

    @staticmethod
    async def _retrieve_population(task_id: str) -> float:
        response = await TaskResultsRetriever(task_id=task_id).retrieve()
        return response.data['total_population']


@then("the population in the area should be 6,384,440")
@async_run_until_complete
async def step_impl(context: ContextPopulation):
    """
    Args:
        context (behave.runner.Context):
    """
    expected_population = 8968197.11
    population = await PopulationRetriever(area=context.area).retrieve()
    assert population == expected_population, f'{population} != {expected_population}'
