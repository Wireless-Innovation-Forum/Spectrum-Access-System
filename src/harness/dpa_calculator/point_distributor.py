import random
from dataclasses import dataclass
from typing import List

from dpa_calculator.utils import Point
from reference_models.geo.vincenty import GeodesicPoint


@dataclass
class AreaCircle:
    center_coordinates: Point
    radius_in_kilometers: int


class PointDistributor:
    _max_bearing = 360

    def __init__(self, distribution_area: AreaCircle):
        self._distribution_area = distribution_area

    def distribute_points(self, number_of_points: int) -> List[Point]:
        return [self._generate_point() for _ in range(number_of_points)]

    def _generate_point(self) -> Point:
        random_distance = random.random() * self._max_distance
        random_bearing = random.random() * self._max_bearing
        coordinates = GeodesicPoint(lat=self._origin.latitude, lon=self._origin.longitude, dist_km=random_distance, bearing=random_bearing)
        return Point(latitude=coordinates[0], longitude=coordinates[1])

    @property
    def _max_distance(self) -> float:
        return self._distribution_area.radius_in_kilometers

    @property
    def _origin(self) -> Point:
        return self._distribution_area.center_coordinates
