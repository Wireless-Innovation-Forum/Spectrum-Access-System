from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import Type

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator import \
    AntennaGainCalculator
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator_gain_pattern import \
    AntennaGainCalculatorGainPattern
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.antenna_gain_calculator.antenna_gain_calculator_standard import \
    AntennaGainCalculatorStandard
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.cbsds_creator.cbsds_generator import CbsdsWithBearings
from cu_pass.dpa_calculator.dpa.dpa import Dpa


class ReceiveAntennaGainTypes(Enum):
    pattern = auto()
    standard = auto()


class AggregateInterferenceCalculator(ABC):
    def __init__(self,
                 cbsds_with_bearings: CbsdsWithBearings,
                 dpa: Dpa,
                 receive_antenna_gain_calculator_type: ReceiveAntennaGainTypes = ReceiveAntennaGainTypes.pattern):
        self._bearings = cbsds_with_bearings.bearings
        self._cbsds = cbsds_with_bearings.cbsds
        self._dpa = dpa
        self._receive_antenna_gain_calculator_type = receive_antenna_gain_calculator_type

    @abstractmethod
    def calculate(self, distance: float, cbsd_category: CbsdCategories) -> float:
        pass

    @abstractmethod
    def get_expected_interference(self, distance: float, cbsd_category: CbsdCategories) -> float:
        pass

    @property
    def _receive_antenna_gain_calculator_class(self) -> Type[AntennaGainCalculator]:
        map = {
            ReceiveAntennaGainTypes.pattern: AntennaGainCalculatorGainPattern,
            ReceiveAntennaGainTypes.standard: AntennaGainCalculatorStandard
        }
        return map[self._receive_antenna_gain_calculator_type]
