from dataclasses import dataclass

from dpa_calculator.constants import REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN


@dataclass
class HeightDistribution:
    maximum_height_in_meters: int
    minimum_height_in_meters: int
    fraction_of_cbsds: float


OUTDOOR_AP_HEIGHT_IN_METERS = 6


INDOOR_AP_HEIGHT_DISTRIBUTION = {
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
