from dataclasses import dataclass
from typing import List

from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from dpa_calculator.utilities import Point
from reference_models.dpa.dpa_builder import ProtectionPoint
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import calcAggregatedInterference


class AggregateInterferenceCalculatorNtia(AggregateInterferenceCalculator):
    def calculate(self) -> float:
        point = Point.from_shapely(point_shapely=self._dpa.geometry.centroid)

    # @property
    # def interference_information(self) -> List[InterferenceComponents]:
    #     return [
    #         InterferenceComponents(
    #             eirp=grant.max_eirp,
    #             frequency_dependent_rejection=0,
    #             gain_receiver=0,
    #             loss_building=0,
    #             loss_clutter=0,
    #             loss_propagation=0,
    #             loss_receiver=INSERTION_LOSSES_IN_DB,
    #             loss_transmitter=INSERTION_LOSSES_IN_DB
    #         )
    #         for grant in self._grants
    #     ]
