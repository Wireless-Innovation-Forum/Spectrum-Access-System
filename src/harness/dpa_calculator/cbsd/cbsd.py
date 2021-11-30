from dataclasses import dataclass

from dpa_calculator.constants import REGION_TYPE_RURAL
from dpa_calculator.utilities import get_distance_between_two_points, get_region_type, Point
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import FREQ_PROP_MODEL
from reference_models.geo.drive import nlcd_driver
from reference_models.propagation.ehata import ehata
from reference_models.propagation.wf_itm import CalcItmPropagationLoss

PROPAGATION_LOSS_HEIGHT_CUTOFF = 18

INSERTION_LOSSES_IN_DB = 2


@dataclass
class InterferenceComponents:
    eirp: float
    frequency_dependent_rejection: float
    gain_receiver: float
    loss_building: float
    loss_clutter: float
    loss_propagation: float
    loss_receiver: float
    loss_transmitter: float


@dataclass
class Cbsd:
    eirp: float = None
    gain: int = None
    height: float = None
    is_indoor: bool = None
    location: Point = None

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
                             max_eirp=self.eirp)

    def calculate_interference(self, dpa: Dpa):
        dpa_center = Point.from_shapely(point_shapely=dpa.geometry.centroid)
        propagation_loss_itm = CalcItmPropagationLoss(
          lat_cbsd=self.location.latitude,
          lon_cbsd=self.location.longitude,
          height_cbsd=self.height,
          lat_rx=dpa_center.latitude,
          lon_rx=dpa_center.longitude,
          height_rx=dpa.radar_height,
          cbsd_indoor=self.is_indoor,
          freq_mhz=FREQ_PROP_MODEL).db_loss
        propagation_loss_ehata = ehata.MedianBasicPropLoss(
            freq_mhz=FREQ_PROP_MODEL,
            height_tx=self.height,
            height_rx=dpa.radar_height,
            dist_km=get_distance_between_two_points(point1=self.location, point2=dpa_center),
            region_code=nlcd_driver.GetLandCoverCodes(lat=dpa_center.latitude, lon=dpa_center.longitude)
        )
        should_use_itm = self.height >= PROPAGATION_LOSS_HEIGHT_CUTOFF or get_region_type(coordinates=dpa_center) == REGION_TYPE_RURAL
        return InterferenceComponents(
                eirp=self.eirp,
                frequency_dependent_rejection=0,
                gain_receiver=0,
                loss_building=0,
                loss_clutter=0,
                loss_propagation=propagation_loss_itm if should_use_itm else max(propagation_loss_itm, propagation_loss_ehata),
                loss_receiver=INSERTION_LOSSES_IN_DB,
                loss_transmitter=INSERTION_LOSSES_IN_DB
            )
