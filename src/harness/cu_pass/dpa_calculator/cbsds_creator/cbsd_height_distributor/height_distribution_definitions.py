from dataclasses import dataclass
from typing import List

from cu_pass.dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution_uniform import \
    FractionalDistributionUniform


@dataclass
class HeightDistribution:
    maximum_height_in_meters: float
    minimum_height_in_meters: float
    fraction_of_cbsds: float

    def to_fractional_distribution(self) -> FractionalDistribution:
        return FractionalDistributionUniform(
            range_maximum=self.maximum_height_in_meters,
            range_minimum=self.minimum_height_in_meters,
            fraction=self.fraction_of_cbsds
        )


def fractional_distribution_to_height_distribution(distribution: FractionalDistribution) -> HeightDistribution:
    return HeightDistribution(
        maximum_height_in_meters=distribution.range_maximum,
        minimum_height_in_meters=distribution.range_minimum,
        fraction_of_cbsds=distribution.fraction
    )


OUTDOOR_UE_HEIGHT_IN_METERS = 1.5

INDOOR_UE_HEIGHT_DIFFERENCE_FROM_AP = 1.5


INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A = {
    REGION_TYPE_DENSE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=15,
            minimum_height_in_meters=3,
            fraction_of_cbsds=0.5
        ),
        HeightDistribution(
            maximum_height_in_meters=30,
            minimum_height_in_meters=18,
            fraction_of_cbsds=0.25
        ),
        HeightDistribution(
            maximum_height_in_meters=60,
            minimum_height_in_meters=33,
            fraction_of_cbsds=0.25
        ),
    ],
    REGION_TYPE_RURAL: [
        HeightDistribution(
            maximum_height_in_meters=3,
            minimum_height_in_meters=3,
            fraction_of_cbsds=0.8
        ),
        HeightDistribution(
            maximum_height_in_meters=6,
            minimum_height_in_meters=6,
            fraction_of_cbsds=0.2
        ),
    ],
    REGION_TYPE_SUBURBAN: [
        HeightDistribution(
            maximum_height_in_meters=3,
            minimum_height_in_meters=3,
            fraction_of_cbsds=0.7
        ),
        HeightDistribution(
            maximum_height_in_meters=12,
            minimum_height_in_meters=6,
            fraction_of_cbsds=0.3
        )
    ],
    REGION_TYPE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=3,
            minimum_height_in_meters=3,
            fraction_of_cbsds=0.5
        ),
        HeightDistribution(
            maximum_height_in_meters=18,
            minimum_height_in_meters=6,
            fraction_of_cbsds=0.5
        )
    ]
}


OUTDOOR_UE_HEIGHT_DISTRIBUTION = {
    REGION_TYPE_DENSE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            minimum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_RURAL: [
        HeightDistribution(
            maximum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            minimum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_SUBURBAN: [
        HeightDistribution(
            maximum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            minimum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            minimum_height_in_meters=OUTDOOR_UE_HEIGHT_IN_METERS,
            fraction_of_cbsds=1
        ),
    ]
}


OUTDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_B = {
    REGION_TYPE_DENSE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=30,
            minimum_height_in_meters=6,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_RURAL: [
        HeightDistribution(
            maximum_height_in_meters=100,
            minimum_height_in_meters=6,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_SUBURBAN: [
        HeightDistribution(
            maximum_height_in_meters=100,
            minimum_height_in_meters=6,
            fraction_of_cbsds=1
        ),
    ],
    REGION_TYPE_URBAN: [
        HeightDistribution(
            maximum_height_in_meters=30,
            minimum_height_in_meters=6,
            fraction_of_cbsds=1
        ),
    ]
}


def _get_indoor_ue_height_distribution(associated_ap_distribution: HeightDistribution) -> HeightDistribution:
    return HeightDistribution(
        maximum_height_in_meters=associated_ap_distribution.maximum_height_in_meters - INDOOR_UE_HEIGHT_DIFFERENCE_FROM_AP,
        minimum_height_in_meters=associated_ap_distribution.minimum_height_in_meters - INDOOR_UE_HEIGHT_DIFFERENCE_FROM_AP,
        fraction_of_cbsds=associated_ap_distribution.fraction_of_cbsds
    )


def _get_indoor_ue_height_distributions(associated_ap_distributions: List[HeightDistribution]) -> List[HeightDistribution]:
    return [_get_indoor_ue_height_distribution(associated_ap_distribution=distribution) for distribution in associated_ap_distributions]


INDOOR_UE_HEIGHT_DISTRIBUTION = {region_type: _get_indoor_ue_height_distributions(associated_ap_distributions=distributions)
                                 for region_type, distributions in INDOOR_AP_HEIGHT_DISTRIBUTION_CATEGORY_A.items()}
