from abc import ABC

from cu_pass.dpa_calculator.aggregate_interference_calculator.configuration.configuration_manager import \
    ConfigurationManager
from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd, CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger, Point

GAIN_AP = 6
GAIN_UE = 0


class CbsdBuilder(ABC):
    def __init__(self,
                 category: CbsdCategories,
                 cbsd_type: CbsdTypes,
                 dpa_region_type: str,
                 height: float,
                 is_indoor: bool,
                 location: Point):
        self._category = category
        self._cbsd_type = cbsd_type
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
    def _eirp_maximum(self) -> float:
        configuration = ConfigurationManager().get_configuration()
        distribution = configuration.eirp_distribution[self._cbsd_type][self._category][self._dpa_region_type][self._is_indoor]
        self._log_distribution(distribution=distribution)
        return distribution.get_values(number_of_values=1)[0]

    @staticmethod
    def _log_distribution(distribution: FractionalDistribution) -> None:
        logger = get_dpa_calculator_logger()
        logger.info(f"\t\t\tEIRP Distribution: {distribution}")

    @property
    def _gain(self) -> int:
        if self._is_user_equipment:
            return GAIN_UE
        else:
            return GAIN_AP

    @property
    def _is_category_a(self) -> bool:
        return self._category == CbsdCategories.A

    @property
    def _is_user_equipment(self) -> bool:
        return self._cbsd_type == CbsdTypes.UE
