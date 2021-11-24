from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

from dpa_calculator.utils import Point
from reference_models.common.data import CbsdGrantInfo

CBSD_A_INDICATOR = 'A'
CBSD_B_INDICATOR = 'B'
EIRP_AP_INDOOR = 26
EIRP_AP_OUTDOOR = 30
GAIN_AP = 6
GAIN_UE = 0


@dataclass
class Cbsd:
    gain: int = None
    height: float = None
    is_indoor: bool = None
    location: Point = None
    transmit_power: float = None

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


class CbsdGetter(ABC):
    def __init__(self, category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], height: float, is_indoor: bool, location: Point):
        self._category = category
        self._height = height
        self._is_indoor = is_indoor
        self._location = location

    def get(self) -> Cbsd:
        return Cbsd(gain=self._gain,
                    height=self._height,
                    is_indoor=self._is_indoor,
                    transmit_power=self._eirp,
                    location=self._location)

    @property
    @abstractmethod
    def _gain(self) -> int:
        raise NotImplementedError

    @property
    def _eirp(self) -> int:
        return EIRP_AP_INDOOR if self._is_indoor else EIRP_AP_OUTDOOR


class CbsdGetterAp(CbsdGetter):
    @property
    def _gain(self) -> int:
        return GAIN_AP


class CbsdGetterUe(CbsdGetter):
    @property
    def _gain(self) -> int:
        return GAIN_UE


def get_cbsd_ap(category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], height: float, is_indoor: bool, location: Point) -> Cbsd:
    return CbsdGetterAp(category=category, height=height, is_indoor=is_indoor, location=location).get()


def get_cbsd_ue(category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], height: float, is_indoor: bool, location: Point) -> Cbsd:
    return CbsdGetterUe(category=category, height=height, is_indoor=is_indoor, location=location).get()
