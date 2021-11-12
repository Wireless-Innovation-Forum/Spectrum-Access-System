from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import ContextManager, Union

import worldpop_client
from worldpop_client.api import services_api, tasks_api


class WorldPopCommunicator(ABC):
    @property
    @contextmanager
    @abstractmethod
    def _api(self) -> Union[services_api.ServicesApi, tasks_api.TasksApi]:
        raise NotImplementedError

    @property
    @contextmanager
    def _worldpop_api_client(self) -> ContextManager[worldpop_client.ApiClient]:
        with worldpop_client.ApiClient() as api_client:
            yield api_client
