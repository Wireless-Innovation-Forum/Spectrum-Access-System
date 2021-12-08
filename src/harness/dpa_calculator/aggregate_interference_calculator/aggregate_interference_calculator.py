from abc import ABC, abstractmethod
from typing import List, Type

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.antenna_gain_calculator.antenna_gain_calculator_uniform import \
    AntennaGainCalculatorUniform
from dpa_calculator.cbsd.cbsd import Cbsd
from reference_models.dpa.dpa_mgr import Dpa


class AggregateInterferenceCalculator(ABC):
    def __init__(self,
                 cbsds: List[Cbsd],
                 dpa: Dpa,
                 receive_antenna_gain_calculator_class: Type[AntennaGainCalculator] = AntennaGainCalculatorUniform):
        self._cbsds = cbsds
        self._dpa = dpa
        self._receive_antenna_gain_calculator_class = receive_antenna_gain_calculator_class

    @abstractmethod
    def calculate(self, minimum_distance: float) -> float:
        raise NotImplementedError
