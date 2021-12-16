import random

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.cbsd_interference_calculator.variables import \
    CLUTTER_LOSS_MAXIMUM, CLUTTER_LOSS_MINIMUM, INSERTION_LOSSES_IN_DB, InterferenceComponents, \
    LOADING_FRACTIONS
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator_ntia.helpers.propagation_loss_calculator import \
    PropagationLossCalculator
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdTypes
from cu_pass.dpa_calculator.utilities import get_distance_between_two_points, get_dpa_center, \
    get_region_type, Point, region_is_rural
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.interference.interference import dbToLinear, linearToDb


class CbsdInterferenceCalculator:
    def __init__(self, cbsd: Cbsd, dpa: Dpa):
        self._cbsd = cbsd
        self._dpa = dpa

    def calculate(self) -> InterferenceComponents:
        return InterferenceComponents(
            distance_in_kilometers=get_distance_between_two_points(point1=self._dpa_center, point2=self._cbsd.location),
            eirp=self._eirp,
            frequency_dependent_rejection=0,
            loss_clutter=random.uniform(CLUTTER_LOSS_MINIMUM,
                                        CLUTTER_LOSS_MAXIMUM) if self._is_rural else CLUTTER_LOSS_MINIMUM,
            loss_propagation=PropagationLossCalculator(cbsd=self._cbsd, dpa=self._dpa).calculate(),
            loss_receiver=INSERTION_LOSSES_IN_DB,
            loss_transmitter=INSERTION_LOSSES_IN_DB if self._has_transmitter_losses else 0
        )

    @property
    def _eirp(self) -> float:
        loading_fraction = LOADING_FRACTIONS[self._region_type]
        power_in_milliwatts = dbToLinear(self._cbsd.eirp_maximum)
        fractional_power = power_in_milliwatts * loading_fraction
        power_in_dbm = linearToDb(fractional_power)
        return round(power_in_dbm, 1)

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._dpa_center)

    @property
    def _has_transmitter_losses(self) -> bool:
        return not self._cbsd.is_indoor and self._cbsd.cbsd_type == CbsdTypes.AP

    @property
    def _is_rural(self) -> bool:
        return region_is_rural(coordinates=self._dpa_center)

    @property
    def _dpa_center(self) -> Point:
        return get_dpa_center(dpa=self._dpa)
