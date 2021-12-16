from abc import ABC, abstractmethod

from cu_pass.dpa_calculator.point_distributor import AreaCircle


class PopulationRetriever(ABC):
    def __init__(self, area: AreaCircle):
        self._area = area

    @abstractmethod
    def retrieve(self) -> int:
        raise NotImplementedError
