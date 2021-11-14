from dataclasses import dataclass
from typing import Union

import parse
from behave import *

from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import BuildDpa
from reference_models.geo.drive import nlcd_driver
from reference_models.geo.nlcd import GetRegionType

CBSD_A_INDICATOR = 'A'
CBSD_B_INDICATOR = 'B'

REGION_TYPE_RURAL = 'RURAL'


@dataclass
class Cbsd:
    height: float
    is_indoor: bool
    location: Point
    transmit_power: float

    def to_grant(self, low_frequency: float, high_frequency: float) -> CbsdGrantInfo:
        return CbsdGrantInfo(antenna_azimuth=None,
                             antenna_beamwidth=None,
                             antenna_gain=6,
                             cbsd_category=None,
                             height_agl=self.height,
                             high_frequency=high_frequency,
                             indoor_deployment=self.is_indoor,
                             is_managed_grant=None,
                             latitude=self.location.latitude,
                             longitude=self.location.longitude,
                             low_frequency=low_frequency,
                             max_eirp=self.transmit_power)

    @property
    def region_type(self) -> str:
        cbsd_region_code = nlcd_driver.GetLandCoverCodes(self.location.latitude,
                                                         self.location.longitude)
        return GetRegionType(cbsd_region_code)


def get_cbsd_ap(category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], is_indoor: bool, location: Point) -> Cbsd:
    return Cbsd(height=6, is_indoor=is_indoor, transmit_power=30, location=location)


# @dataclass
# class CbsdB(Cbsd):
#     transmit_power = 47


@parse.with_pattern(f'({CBSD_A_INDICATOR}|{CBSD_B_INDICATOR})')
def parse_cbsd(text: str) -> Cbsd:
    pass
    # if text == CBSD_A_INDICATOR:
    #     return Ap()
    # else:
    #     return CbsdB()


@parse.with_pattern('.*')
def parse_dpa(text: str):
    return BuildDpa(dpa_name=text.upper())


register_type(Cbsd=parse_cbsd)
register_type(Dpa=parse_dpa)
