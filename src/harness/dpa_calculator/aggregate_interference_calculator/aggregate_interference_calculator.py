from abc import ABC, abstractmethod
from typing import Type

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator_gain_pattern import \
    AntennaGainCalculatorGainPattern
from dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from dpa_calculator.dpa.dpa import Dpa


class AggregateInterferenceCalculator(ABC):
    def __init__(self,
                 cbsds_with_bearings: CbsdsWithBearings,
                 dpa: Dpa,
                 receive_antenna_gain_calculator_class: Type[AntennaGainCalculator] = AntennaGainCalculatorGainPattern):
        self._bearings = cbsds_with_bearings.bearings
        self._cbsds = cbsds_with_bearings.cbsds
        self._dpa = dpa
        self._receive_antenna_gain_calculator_class = receive_antenna_gain_calculator_class

    @abstractmethod
    def calculate(self, minimum_distance: float) -> float:
        raise NotImplementedError
