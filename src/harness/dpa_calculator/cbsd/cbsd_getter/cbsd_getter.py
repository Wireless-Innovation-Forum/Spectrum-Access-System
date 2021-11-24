from abc import ABC, abstractmethod
from typing import Union

from dpa_calculator.cbsd.cbsd import Cbsd
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
        return Cbsd(eirp=self._eirp,
                    gain=self._gain,
                    height=self._height,
                    is_indoor=self._is_indoor,
                    location=self._location)

    @property
    @abstractmethod
    def _gain(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def _eirp(self) -> int:
        raise NotImplementedError
