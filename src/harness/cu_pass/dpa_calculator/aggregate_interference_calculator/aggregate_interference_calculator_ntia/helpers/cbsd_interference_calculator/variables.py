from dataclasses import dataclass
from typing import Dict

from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN

CLUTTER_LOSS_MAXIMUM = 15
CLUTTER_LOSS_MINIMUM = 0
INSERTION_LOSSES_IN_DB = 2


LOADING_FRACTIONS = {
    REGION_TYPE_DENSE_URBAN: 0.6,
    REGION_TYPE_RURAL: 0.2,
    REGION_TYPE_SUBURBAN: 0.4,
    REGION_TYPE_URBAN: 0.6
}


@dataclass
class GainAtAzimuth:
    azimuth: float
    gain: float


@dataclass
class InterferenceComponents:
    distance_in_kilometers: float
    eirp: float
    frequency_dependent_rejection: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float

    gain_receiver: Dict[float, GainAtAzimuth] = None
    loss_building: float = None

    def total_interference(self, azimuth: float) -> float:
        receiver_gain = self.gain_receiver[azimuth].gain
        return self.eirp \
               + receiver_gain \
               - self.loss_transmitter \
               - self.loss_receiver \
               - self.loss_propagation \
               - self.loss_clutter \
               - self.loss_building \
               - self.frequency_dependent_rejection
