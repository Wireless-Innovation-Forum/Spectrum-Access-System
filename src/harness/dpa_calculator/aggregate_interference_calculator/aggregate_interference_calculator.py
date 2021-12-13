from abc import ABC, abstractmethod
from typing import List, Type

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator_gain_pattern import \
    AntennaGainCalculatorGainPattern
from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.dpa.dpa import Dpa


class AggregateInterferenceCalculator(ABC):
    def __init__(self,
                 cbsds: List[Cbsd],
                 dpa: Dpa,
                 receive_antenna_gain_calculator_class: Type[AntennaGainCalculator] = AntennaGainCalculatorGainPattern):
        self._cbsds = cbsds
        self._dpa = dpa
        self._receive_antenna_gain_calculator_class = receive_antenna_gain_calculator_class

    @abstractmethod
    def calculate(self, minimum_distance: float) -> float:
        raise NotImplementedError
