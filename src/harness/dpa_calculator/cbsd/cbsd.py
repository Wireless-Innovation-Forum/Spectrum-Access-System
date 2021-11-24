from dataclasses import dataclass

from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo


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
