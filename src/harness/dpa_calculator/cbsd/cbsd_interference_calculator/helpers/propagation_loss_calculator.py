from dpa_calculator.utilities import get_distance_between_two_points, get_dpa_center, Point, region_is_rural
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import FREQ_PROP_MODEL
from reference_models.geo.drive import nlcd_driver
from reference_models.propagation.ehata import ehata
from reference_models.propagation.wf_itm import CalcItmPropagationLoss

PROPAGATION_LOSS_HEIGHT_CUTOFF = 18


class PropagationLossCalculator:
    def __init__(self, cbsd: 'Cbsd', dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> float:
        return self._propagation_loss_itm if self._should_use_itm else max(self._propagation_loss_itm,
                                                                           self._propagation_loss_ehata)

    @property
    def _propagation_loss_itm(self) -> float:
        return CalcItmPropagationLoss(
            lat_cbsd=self._cbsd.location.latitude,
            lon_cbsd=self._cbsd.location.longitude,
            height_cbsd=self._cbsd.height_in_meters,
            lat_rx=self._dpa_center.latitude,
            lon_rx=self._dpa_center.longitude,
            height_rx=self._dpa.radar_height,
            cbsd_indoor=self._cbsd.is_indoor,
            freq_mhz=FREQ_PROP_MODEL).db_loss

    @property
    def _should_use_itm(self) -> bool:
        is_rural = region_is_rural(coordinates=self._dpa_center)
        is_tall = self._cbsd.height_in_meters >= PROPAGATION_LOSS_HEIGHT_CUTOFF
        return is_tall or is_rural

    @property
    def _propagation_loss_ehata(self):
        return ehata.MedianBasicPropLoss(
            freq_mhz=FREQ_PROP_MODEL,
            height_tx=self._cbsd.height_in_meters,
            height_rx=self._dpa.radar_height,
            dist_km=get_distance_between_two_points(point1=self._cbsd.location, point2=(self._dpa_center)),
            region_code=nlcd_driver.GetLandCoverCodes(lat=self._dpa_center.latitude, lon=self._dpa_center.longitude)
        )

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
