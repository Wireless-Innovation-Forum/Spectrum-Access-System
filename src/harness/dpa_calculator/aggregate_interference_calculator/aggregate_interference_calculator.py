from abc import ABC, abstractmethod
from typing import List

from dpa_calculator.cbsd.cbsd import Cbsd
from reference_models.dpa.dpa_mgr import Dpa


class AggregateInterferenceCalculator(ABC):
    def __init__(self, dpa: Dpa, cbsds: List[Cbsd]):
        self._dpa = dpa
        self._cbsds = cbsds

    @abstractmethod
    def calculate(self) -> float:
        raise NotImplementedError
