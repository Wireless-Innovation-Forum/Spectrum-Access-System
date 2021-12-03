from dataclasses import dataclass
from enum import auto, Enum

from dpa_calculator.utilities import Point
from reference_models.common.data import CbsdGrantInfo


class CbsdTypes(Enum):
    AP = auto()
    UE = auto()


@dataclass
class Cbsd:
    cbsd_type: CbsdTypes = None
    eirp: float = None
    gain: int = None
    height_in_meters: float = None
    is_indoor: bool = None
    location: Point = None

    def to_grant(self) -> CbsdGrantInfo:
        return CbsdGrantInfo(antenna_azimuth=None,
                             antenna_beamwidth=None,
                             antenna_gain=self.gain,
                             cbsd_category=None,
                             height_agl=self.height_in_meters,
                             high_frequency=None,
                             indoor_deployment=self.is_indoor,
                             is_managed_grant=None,
                             latitude=self.location.latitude,
                             longitude=self.location.longitude,
                             low_frequency=None,
                             max_eirp=self.eirp)
