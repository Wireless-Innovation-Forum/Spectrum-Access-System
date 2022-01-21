from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_APS_FOR_POPULATION_TYPE, \
    NumberOfApsCalculator
from cu_pass.dpa_calculator.utilities import get_region_type


NUMBER_OF_UES_PER_AP_BY_REGION_TYPE = {
    CbsdCategories.A: {
        REGION_TYPE_DENSE_URBAN: 50,
        REGION_TYPE_RURAL: 3,
        REGION_TYPE_SUBURBAN: 20,
        REGION_TYPE_URBAN: 50
    },
    CbsdCategories.B: {
        REGION_TYPE_DENSE_URBAN: 200,
        REGION_TYPE_RURAL: 500,
        REGION_TYPE_SUBURBAN: 200,
        REGION_TYPE_URBAN: 200
    }
}


FRACTION_OF_USERS_SERVED_BY_APS = {
    CbsdCategories.A: {
        REGION_TYPE_DENSE_URBAN: .8,
        REGION_TYPE_RURAL: .4,
        REGION_TYPE_SUBURBAN: .6,
        REGION_TYPE_URBAN: .8
    },
    CbsdCategories.B: {
        REGION_TYPE_DENSE_URBAN: .2,
        REGION_TYPE_RURAL: .6,
        REGION_TYPE_SUBURBAN: .4,
        REGION_TYPE_URBAN: .2
    }
}


class NumberOfApsCalculatorShipborne(NumberOfApsCalculator):
    _channel_scaling_factor = 0.1
    _market_penetration_factor = 0.2

    def get_number_of_aps(self) -> NUMBER_OF_APS_FOR_POPULATION_TYPE:
        number_cat_a = self._number_of_aps_exact(category=CbsdCategories.A)
        number_cat_b = self._number_of_aps_exact(category=CbsdCategories.B)
        return {
            CbsdCategories.A: round(number_cat_a),
            CbsdCategories.B: round(number_cat_b)
        }

    def _number_of_aps_exact(self, category: CbsdCategories) -> float:
        return self._population_to_serve \
               * self._fraction_of_population_served_by_ap(category=category) \
               / self._number_of_users_served_per_ap(category=category)

    @property
    def _population_to_serve(self) -> float:
        return self._simulation_population * self._market_penetration_factor * self._channel_scaling_factor

    def _fraction_of_population_served_by_ap(self, category: CbsdCategories) -> float:
        return FRACTION_OF_USERS_SERVED_BY_APS[category][self._region_type]

    def _number_of_users_served_per_ap(self, category: CbsdCategories) -> int:
        return NUMBER_OF_UES_PER_AP_BY_REGION_TYPE[category][self._region_type]

    @property
    def _region_type(self) -> str:
        return get_region_type(coordinates=self._center_coordinates)
