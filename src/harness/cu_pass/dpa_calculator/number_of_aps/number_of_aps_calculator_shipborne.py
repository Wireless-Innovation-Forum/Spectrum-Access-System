from math import ceil

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_CBSDS_PER_CATEGORY_TYPE, \
    NUMBER_OF_CBSDS_TYPE, NumberOfCbsdsCalculator


class NumberOfCbsdsCalculatorShipborne(NumberOfCbsdsCalculator):
    _channel_scaling_factor = 0.1
    _market_penetration_factor = 0.2

    def get_number_of_cbsds(self) -> NUMBER_OF_CBSDS_PER_CATEGORY_TYPE:
        number_of_category_a = self._get_number_of_cbsds(category=CbsdCategories.A)
        number_of_category_b = self._get_number_of_cbsds(category=CbsdCategories.B)
        return {
            CbsdCategories.A: number_of_category_a,
            CbsdCategories.B: number_of_category_b
        }

    def _get_number_of_cbsds(self, category: CbsdCategories) -> NUMBER_OF_CBSDS_TYPE:
        number_of_ues_exact = self._get_number_of_ues_exact(category=category)
        return {
            CbsdTypes.AP: ceil(number_of_ues_exact / self.get_number_of_users_served_per_ap(category=category)),
            CbsdTypes.UE: round(number_of_ues_exact),
        }

    def _get_number_of_ues_exact(self, category: CbsdCategories) -> float:
        return self._population_to_serve * self.get_fraction_of_population_served_by_ap(category=category)

    @property
    def _population_to_serve(self) -> float:
        return self._simulation_population * self._market_penetration_factor * self._channel_scaling_factor
