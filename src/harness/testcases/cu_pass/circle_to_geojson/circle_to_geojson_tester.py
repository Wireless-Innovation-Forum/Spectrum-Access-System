from abc import ABC, abstractmethod
from typing import List

import numpy
from worldpop_client.model.geo_json import GeoJson

from dpa_calculator.circle_to_geojson_converter import CircleToGeoJsonConverter
from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point


class CircleToGeoJsonTester(ABC):
    _center = Point(latitude=0, longitude=0)
    _north_coordinate = 1.3565516705216198
    _radius_in_kilometers = 150

    def test_coordinates_are_expected(self):
        assert numpy.allclose(self._coordinates, self._expected_coordinates)

    def test_polygon_is_closed(self):
        assert self._coordinates[0] == self._coordinates[-1]

    @property
    def _coordinates(self) -> List[List[float]]:
        return self._geojson.features[0].geometry.coordinates[0]

    @property
    def _geojson(self) -> GeoJson:
        return self._circle_to_geojson_converter.convert()

    @property
    @abstractmethod
    def _expected_coordinates(self) -> List[List[float]]:
        raise NotImplementedError

    @property
    def _circle_to_geojson_converter(self) -> CircleToGeoJsonConverter:
        return CircleToGeoJsonConverter(area=self._area, number_of_points=self._number_of_points)

    @property
    def _area(self) -> AreaCircle:
        return AreaCircle(
            center_coordinates=self._center,
            radius_in_kilometers=self._radius_in_kilometers
        )

    @property
    @abstractmethod
    def _number_of_points(self) -> int:
        raise NotImplementedError

    @property
    def _south_coordinate(self) -> float:
        return -self._north_coordinate
