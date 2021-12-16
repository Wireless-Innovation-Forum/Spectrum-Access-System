import random
from dataclasses import dataclass
from typing import List

from cu_pass.dpa_calculator.utilities import Point, move_distance


@dataclass
class AreaCircle:
    center_coordinates: Point
    radius_in_kilometers: int


@dataclass
class CoordinatesWithBearing:
    bearing: float
    coordinates: Point


class PointDistributor:
    _max_bearing = 360

    def __init__(self, distribution_area: AreaCircle, minimum_distance: int = 0):
        self._distribution_area = distribution_area
        self._minimum_distance = minimum_distance

    def distribute_points(self, number_of_points: int) -> List[CoordinatesWithBearing]:
        return [self._generate_point() for _ in range(number_of_points)]

    def _generate_point(self) -> CoordinatesWithBearing:
        random_distance = random.uniform(self._minimum_distance, self._max_distance)
        random_bearing = random.random() * self._max_bearing
        coordinates = move_distance(bearing=random_bearing, kilometers=random_distance, origin=self._origin)
        return CoordinatesWithBearing(
            bearing=random_bearing,
            coordinates=coordinates
        )

    @property
    def _max_distance(self) -> float:
        return self._distribution_area.radius_in_kilometers

    @property
    def _origin(self) -> Point:
        return self._distribution_area.center_coordinates
