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

    def to_grant(self) -> CbsdGrantInfo:
        return CbsdGrantInfo(latitude=self.location.latitude,
                             longitude=self.location.longitude,
                             height_agl=self.height,
                             indoor_deployment=self.is_indoor,
                             antenna_gain=6,
                             max_eirp=self.transmit_power,
                             cbsd_category=None,
                             antenna_azimuth=None,
                             antenna_beamwidth=None,
                             low_frequency=None,
                             high_frequency=None,
                             is_managed_grant=None)

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
