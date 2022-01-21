from abc import ABC, abstractmethod

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.utilities import Point


class CbsdGetter(ABC):
    def __init__(self, category: CbsdCategories, dpa_region_type: str, height: float, is_indoor: bool, location: Point):
        self._category = category
        self._dpa_region_type = dpa_region_type
        self._height = height
        self._is_indoor = is_indoor
        self._location = location

    def get(self) -> Cbsd:
        return Cbsd(cbsd_category=self._category,
                    cbsd_type=self._cbsd_type,
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
