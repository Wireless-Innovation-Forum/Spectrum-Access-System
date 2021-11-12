from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Iterable

from worldpop_client.api import tasks_api
from worldpop_client.model.tasks_response import TasksResponse

from dpa_calculator.population_retriever.helpers.worldpop_communicator import WorldPopCommunicator


DEFAULT_TIMEOUT = 2
FINISHED_KEY = 'finished'


class TaskResultsRetriever(WorldPopCommunicator):
    def __init__(self, task_id: str):
        self._task_id = task_id

    async def retrieve(self) -> TasksResponse:
        for _ in self._try_before_timeout():
            response = self._ping()
            if response.status == FINISHED_KEY:
                if response.error_message:
                    raise Exception(response.error_message)
                return response

    def _try_before_timeout(self) -> Iterable[None]:
        timeout = datetime.now() + timedelta(minutes=DEFAULT_TIMEOUT)
        while datetime.now() < timeout:
            yield
        raise TimeoutError(self._timeout_message)

    @property
    def _timeout_message(self) -> str:
        return f'Timeout waiting for task {self._task_id}'

    def _ping(self) -> TasksResponse:
        with self._api as api_instance:
            return api_instance.tasks_task_id_get(task_id=self._task_id)

    @property
    @contextmanager
    def _api(self) -> tasks_api.TasksApi:
        with self._worldpop_api_client as api_client:
            yield tasks_api.TasksApi(api_client)
