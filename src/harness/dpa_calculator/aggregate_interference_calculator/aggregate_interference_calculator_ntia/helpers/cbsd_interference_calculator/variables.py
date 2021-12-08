from dataclasses import dataclass
from typing import Dict

CLUTTER_LOSS_MAXIMUM = 15
CLUTTER_LOSS_MINIMUM = 0
INSERTION_LOSSES_IN_DB = 2


@dataclass
class GainAtAzimuth:
    azimuth: float
    gain: float


@dataclass
class InterferenceComponents:
    distance_in_kilometers: float
    eirp: float
    frequency_dependent_rejection: float
    gain_receiver: Dict[float, GainAtAzimuth]
    loss_building: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float

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
