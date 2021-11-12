from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.population_retriever.helpers.task_creator import TaskCreator
from dpa_calculator.population_retriever.helpers.task_results_retriever import TaskResultsRetriever


class PopulationRetriever:
    _TOTAL_POPULATION_KEY = 'total_population'

    def __init__(self, area: AreaCircle):
        self._area = area

    async def retrieve(self) -> float:
        task_id = self._create_task()
        population = await self._retrieve_population(task_id=task_id)
        return round(population)

    def _create_task(self) -> str:
        return TaskCreator(area=self._area).create()

    async def _retrieve_population(self, task_id: str) -> float:
        response = await TaskResultsRetriever(task_id=task_id).retrieve()
        return response.data[self._TOTAL_POPULATION_KEY]
