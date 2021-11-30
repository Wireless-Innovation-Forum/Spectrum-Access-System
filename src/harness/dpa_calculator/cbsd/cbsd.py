from dataclasses import dataclass

from dpa_calculator.cbsd.helpers.propagation_loss_calculator import INSERTION_LOSSES_IN_DB, PropagationLossCalculator
from dpa_calculator.utilities import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa


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


@dataclass
class Cbsd:
    eirp: float = None
    gain: int = None
    height: float = None
    is_indoor: bool = None
    location: Point = None

    def to_grant(self) -> CbsdGrantInfo:
        return CbsdGrantInfo(antenna_azimuth=None,
                             antenna_beamwidth=None,
                             antenna_gain=self.gain,
                             cbsd_category=None,
                             height_agl=self.height,
                             high_frequency=None,
                             indoor_deployment=self.is_indoor,
                             is_managed_grant=None,
                             latitude=self.location.latitude,
                             longitude=self.location.longitude,
                             low_frequency=None,
                             max_eirp=self.eirp)

    def calculate_interference(self, dpa: Dpa):
        return InterferenceComponents(
                eirp=self.eirp,
                frequency_dependent_rejection=0,
                gain_receiver=0,
                loss_building=0,
                loss_clutter=0,
                loss_propagation=PropagationLossCalculator(cbsd=self, dpa=dpa).calculate(),
                loss_receiver=INSERTION_LOSSES_IN_DB,
                loss_transmitter=INSERTION_LOSSES_IN_DB
            )
