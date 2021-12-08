from typing import List, Optional, Tuple

import shapely.geometry
from numpy import ndarray

from dpa_calculator.dpa.utilities import get_uniform_gain_pattern
from reference_models.dpa import dpa_mgr
from reference_models.dpa.dpa_mgr import DPA_DEFAULT_FREQ_RANGE


class Dpa(dpa_mgr.Dpa):
    gain_pattern: Optional[ndarray] = None

    def __init__(self,
                 protected_points,
                 geometry: Optional[shapely.geometry.Point] = None,
                 name: Optional[str] = None,
                 threshold: Optional[float] = None,
                 radar_height: Optional[float] = None,
                 beamwidth: Optional[float] = None,
                 azimuth_range: Tuple[float, float] = None,
                 freq_ranges_mhz: Optional[List[Tuple[float, float]]] = None,
                 neighbor_distances: Optional[Tuple[float, float, float, float]] = None,
                 monitor_type: Optional[str] = None,
                 gain_pattern: Optional[ndarray] = None):
        super().__init__(protected_points=protected_points,
                         geometry=geometry,
                         name=name,
                         threshold=threshold,
                         radar_height=radar_height,
                         beamwidth=beamwidth,
                         azimuth_range=azimuth_range,
                         freq_ranges_mhz=freq_ranges_mhz or [DPA_DEFAULT_FREQ_RANGE],
                         neighbor_distances=neighbor_distances,
                         monitor_type=monitor_type)
        self.gain_pattern = get_uniform_gain_pattern() if gain_pattern is None else gain_pattern

    @classmethod
    def from_winnforum_dpa(cls, dpa: dpa_mgr.Dpa) -> 'Dpa':
        dpa.__class__ = cls
        dpa.gain_pattern = get_uniform_gain_pattern()
        return dpa
