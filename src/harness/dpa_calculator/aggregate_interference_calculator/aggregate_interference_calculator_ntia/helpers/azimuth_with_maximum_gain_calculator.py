from typing import Iterable, List

from numpy import argmax

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator import \
    InterferenceComponents


class InterferenceAtAzimuthWithMaximumGainCalculator:
    def __init__(self, minimum_distance: float, interference_components: List[InterferenceComponents]):
        self._minimum_distance = minimum_distance
        self._interference_components = interference_components

    def calculate(self) -> float:
        total_interferences = [
            sum(component.total_interference(azimuth=azimuth) for component in self._interference_components_in_range)
            for azimuth in self._azimuths
        ]
        return max(total_interferences)

    @property
    def _azimuths(self) -> Iterable[float]:
        return self._interference_components[0].gain_receiver.keys()

    @property
    def _interference_components_in_range(self) -> List[InterferenceComponents]:
        return [components for components in self._interference_components
                if components.distance_in_kilometers >= self._minimum_distance]
