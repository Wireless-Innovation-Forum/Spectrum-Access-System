from dataclasses import dataclass

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.cbsd.cbsd_interference_calculator.helpers.propagation_loss_calculator import \
    PropagationLossCalculator
from reference_models.dpa.dpa_mgr import Dpa

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
            loss_clutter=0,
            loss_propagation=PropagationLossCalculator(cbsd=self._cbsd, dpa=self._dpa).calculate(),
            loss_receiver=INSERTION_LOSSES_IN_DB,
            loss_transmitter=INSERTION_LOSSES_IN_DB
        )
