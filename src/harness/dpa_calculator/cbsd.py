from dataclasses import dataclass
from typing import Union

from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo

AP_GAIN = 6
CBSD_A_INDICATOR = 'A'
CBSD_B_INDICATOR = 'B'


@dataclass
class Cbsd:
    gain: int
    height: float
    is_indoor: bool
    location: Point
    transmit_power: float

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
                             max_eirp=self.transmit_power)


def get_cbsd_ap(category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], height: float, is_indoor: bool, location: Point) -> Cbsd:
    return Cbsd(gain=AP_GAIN, height=height, is_indoor=is_indoor, transmit_power=30, location=location)
