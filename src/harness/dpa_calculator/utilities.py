from statistics import mean
from typing import Callable, Tuple

from shapely import geometry

from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.geo.drive import nlcd_driver
from reference_models.geo.nlcd import LandCoverCodes
from reference_models.geo.vincenty import GeodesicDistanceBearing, GeodesicPoint


class Point:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return geometry.Point(self.latitude, self.longitude) == geometry.Point(other.latitude, other.longitude)

    @classmethod
    def from_shapely(cls, point_shapely: geometry.Point) -> 'Point':
        return cls(latitude=point_shapely.y, longitude=point_shapely.x)

    def to_shapely(self) -> geometry.Point:
        return geometry.Point(self.longitude, self.latitude)


def get_hat_creek_radio_observatory() -> Point:
    return Point(latitude=40.81734, longitude=-121.46933)


def move_distance(bearing: float, kilometers: float, origin: Point) -> Point:
    latitude, longitude, _ = GeodesicPoint(lat=origin.latitude, lon=origin.longitude, dist_km=kilometers, bearing=bearing)
    return Point(latitude=latitude, longitude=longitude)


def get_distance_between_two_points(point1: Point, point2: Point) -> float:
    return _get_geodesic_distance_bearing(point1=point1, point2=point2)[0]


def get_bearing_between_two_points(point1: Point, point2: Point) -> float:
    return _get_geodesic_distance_bearing(point1=point1, point2=point2)[1]


def _get_geodesic_distance_bearing(point1: Point, point2: Point) -> Tuple[float, float, float]:
    return GeodesicDistanceBearing(lat1=point1.latitude, lon1=point1.longitude, lat2=point2.latitude, lon2=point2.longitude)


def get_dpa_center(dpa: Dpa) -> Point:
    return Point.from_shapely(point_shapely=dpa.geometry.centroid)


def get_region_type(coordinates: Point) -> str:
    cbsd_region_code = nlcd_driver.GetLandCoverCodes(lat=coordinates.latitude, lon=coordinates.longitude)

    if cbsd_region_code == LandCoverCodes.DEVELOPED_LOW:
        return REGION_TYPE_SUBURBAN
    elif cbsd_region_code == LandCoverCodes.DEVELOPED_MEDIUM:
        return REGION_TYPE_URBAN
    elif cbsd_region_code == LandCoverCodes.DEVELOPED_HIGH:
        return REGION_TYPE_DENSE_URBAN

    return REGION_TYPE_RURAL


def region_is_rural(coordinates: Point) -> bool:
    return get_region_type(coordinates=coordinates) == REGION_TYPE_RURAL


def run_monte_carlo_simulation(function_to_run: Callable[[], float], number_of_iterations: int) -> float:
    results = []
    for i in range(number_of_iterations):
        print(f'Monte Carlo iteration {i}')
        results.append(function_to_run())
    return mean(results)
