from dataclasses import dataclass
from enum import Enum

from cu_pass.dpa_calculator.utilities import Point
from reference_models.common.data import CbsdGrantInfo


class CbsdCategories(Enum):
    A = 'A'
    B = 'B'


class CbsdTypes(Enum):
    AP = 'AP'
    UE = 'UE'


@dataclass
class Cbsd:
    cbsd_category: CbsdCategories = None
    cbsd_type: CbsdTypes = None
    eirp_maximum: float = None
    gain: int = None
    height_in_meters: float = None
    is_indoor: bool = None
    location: Point = None

    def to_grant(self) -> CbsdGrantInfo:
        return CbsdGrantInfo(antenna_azimuth=None,
                             antenna_beamwidth=None,
                             antenna_gain=self.gain,
                             cbsd_category=self.cbsd_category.name,
                             height_agl=self.height_in_meters,
                             high_frequency=None,
                             indoor_deployment=self.is_indoor,
                             is_managed_grant=None,
                             latitude=self.location.latitude,
                             longitude=self.location.longitude,
                             low_frequency=None,
                             max_eirp=self.eirp_maximum)

    @classmethod
    def from_grant(cls, grant: CbsdGrantInfo):
        return cls(cbsd_category=grant.cbsd_category,
                   eirp_maximum=grant.max_eirp,
                   gain=grant.antenna_gain,
                   height_in_meters=grant.height_agl,
                   is_indoor=grant.indoor_deployment,
                   location=Point(latitude=grant.latitude, longitude=grant.longitude))
