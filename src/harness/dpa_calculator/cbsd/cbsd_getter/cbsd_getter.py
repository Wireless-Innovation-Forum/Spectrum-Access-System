from abc import ABC, abstractmethod
from typing import Union

from dpa_calculator.cbsd.cbsd import Cbsd, CbsdTypes
from dpa_calculator.utilities import Point

CBSD_A_INDICATOR = 'A'
CBSD_B_INDICATOR = 'B'


class CbsdGetter(ABC):
    def __init__(self, category: Union[CBSD_A_INDICATOR, CBSD_B_INDICATOR], height: float, is_indoor: bool, location: Point):
        self._category = category
        self._height = height
        self._is_indoor = is_indoor
        self._location = location

    def get(self) -> Cbsd:
        return Cbsd(cbsd_type=self._cbsd_type,
                    eirp_maximum=self._eirp_maximum,
                    gain=self._gain,
                    height_in_meters=self._height,
                    is_indoor=self._is_indoor,
                    location=self._location)

    @property
    @abstractmethod
    def _cbsd_type(self) -> CbsdTypes:
        raise NotImplementedError

    @property
    @abstractmethod
    def _gain(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def _eirp_maximum(self) -> int:
        raise NotImplementedError
