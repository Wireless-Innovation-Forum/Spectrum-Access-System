import random
from dataclasses import dataclass

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsd.cbsd_interference_calculator.helpers.propagation_loss_calculator import \
    PropagationLossCalculator
from dpa_calculator.utilities import Point, region_is_rural
from reference_models.dpa.dpa_mgr import Dpa

CLUTTER_LOSS_MINIMUM = 0

CLUTTER_LOSS_MAXIMUM = 15

INSERTION_LOSSES_IN_DB = 2


@dataclass
class InterferenceComponents:
    eirp: float
    frequency_dependent_rejection: float
    gain_receiver: float
    loss_building: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float


class CbsdInterferenceCalculator:
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> InterferenceComponents:
        return InterferenceComponents(
            eirp=self._cbsd.eirp,
            frequency_dependent_rejection=0,
            gain_receiver=0,
            loss_building=0,
            loss_clutter=random.uniform(CLUTTER_LOSS_MINIMUM, CLUTTER_LOSS_MAXIMUM) if self._is_rural else CLUTTER_LOSS_MINIMUM,
            loss_propagation=PropagationLossCalculator(cbsd=self._cbsd, dpa=self._dpa).calculate(),
            loss_receiver=INSERTION_LOSSES_IN_DB,
            loss_transmitter=INSERTION_LOSSES_IN_DB
        )

    @property
    def _is_rural(self) -> bool:
        return region_is_rural(coordinates=self._dpa_center)

    @property
    def _dpa_center(self) -> Point:
        return Point.from_shapely(point_shapely=self._dpa.geometry.centroid)
