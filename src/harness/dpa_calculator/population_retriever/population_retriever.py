from abc import ABC, abstractmethod

from dpa_calculator.point_distributor import AreaCircle


class PopulationRetriever(ABC):
    def __init__(self, area: AreaCircle):
        self._area = area

    @abstractmethod
    async def retrieve(self) -> int:
        raise NotImplementedError
