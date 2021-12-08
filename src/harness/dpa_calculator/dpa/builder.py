from enum import Enum
from typing import Union

from dpa_calculator.dpa.dpa import Dpa
from dpa_calculator.dpa.utilities import get_uniform_gain_pattern
from dpa_calculator.utilities import Point
from reference_models.dpa.dpa_mgr import BuildDpa

INTERFERENCE_THRESHOLD_PER_10_MHZ_RADIO_ASTRONOMY = -207


class RadioAstronomyFacilityNames(Enum):
    HatCreek = 'HATCREEK'


CUSTOM_DPA_MAP = {
    RadioAstronomyFacilityNames.HatCreek: Dpa(protected_points=None,
                                              geometry=Point(latitude=40.81734, longitude=-121.46933).to_shapely(),
                                              name=str(RadioAstronomyFacilityNames.HatCreek),
                                              threshold=INTERFERENCE_THRESHOLD_PER_10_MHZ_RADIO_ASTRONOMY,
                                              radar_height=6.1,
                                              beamwidth=3.5,
                                              azimuth_range=(0, 360),
                                              gain_pattern=get_uniform_gain_pattern())
}


def get_dpa(dpa_name: Union[str, RadioAstronomyFacilityNames]) -> Dpa:
    dpa = CUSTOM_DPA_MAP.get(dpa_name, None) or _get_existing_dpa(dpa_name=dpa_name)
    return dpa


def _get_existing_dpa(dpa_name: str) -> Dpa:
    dpa_winnforum = BuildDpa(dpa_name=dpa_name.upper())
    return Dpa.from_winnforum_dpa(dpa=dpa_winnforum)
