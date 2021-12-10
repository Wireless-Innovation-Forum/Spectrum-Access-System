from typing import Iterable, List

from cached_property import cached_property

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    InterferenceComponents
from reference_models.interference.interference import dbToLinear, linearToDb


MILLIWATTS_PER_WATT_IN_DB = 30


class InterferenceAtAzimuthWithMaximumGainCalculator:
    def __init__(self, minimum_distance: float, interference_components: List[InterferenceComponents]):
        self._minimum_distance = minimum_distance
        self._interference_components = interference_components

    def calculate(self) -> float:
        total_interferences = [self._sum_individual_interferences(azimuth=azimuth) for azimuth in self._azimuths]
        return max(total_interferences)

    def _sum_individual_interferences(self, azimuth: float) -> int:
        sum_in_watts = sum(self._convert_dbm_to_watts(dbm=component.total_interference(azimuth=azimuth))
                           for component in self._interference_components_in_range)
        return linearToDb(sum_in_watts)

    @staticmethod
    def _convert_dbm_to_watts(dbm: float) -> float:
        return dbToLinear(dbm - MILLIWATTS_PER_WATT_IN_DB)

    @property
    def _azimuths(self) -> Iterable[float]:
        return self._interference_components[0].gain_receiver.keys()

    @cached_property
    def _interference_components_in_range(self) -> List[InterferenceComponents]:
        return [components for components in self._interference_components
                if components.distance_in_kilometers >= self._minimum_distance]
