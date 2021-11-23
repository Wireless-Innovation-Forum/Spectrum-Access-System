# from contextlib import contextmanager
# from typing import ContextManager
# from unittest import mock
# from unittest.mock import Mock
#
# from worldpop_client.api import services_api, tasks_api
# from worldpop_client.model.stats_response import StatsResponse
# from worldpop_client.model.tasks_response import TasksResponse
#
# ARBITRARY_TASK_ID = 'arbitrary_task_id'
#
#
# @contextmanager
# def mock_worldpop(returned_population: int) -> ContextManager[None]:
#     with mock_stats_get() as stats_get_mock:
#         with mock_tasks_get(expected_population=returned_population) as task_get_mock:
#             yield
#             stats_get_mock.assert_called()
#             task_get_mock.assert_called_with(task_id=ARBITRARY_TASK_ID)
#
#
# @contextmanager
# def mock_stats_get() -> ContextManager[Mock]:
#     with mock.patch.object(services_api.ServicesApi, 'services_stats_get') as stats_get_mock:
#         stats_get_mock.return_value = StatsResponse(
#             status='created',
#             status_code=200,
#             error=False,
#             taskid=ARBITRARY_TASK_ID
#         )
#         yield stats_get_mock
#
#
# @contextmanager
# def mock_tasks_get(expected_population: int) -> ContextManager[Mock]:
#     with mock.patch.object(tasks_api.TasksApi, 'tasks_task_id_get') as task_get_mock:
#         task_get_mock.return_value = TasksResponse(
#             status='finished',
#             status_code=200,
#             error=False,
#             data={
#                 'total_population': expected_population
#             }
#         )
#         yield task_get_mock
