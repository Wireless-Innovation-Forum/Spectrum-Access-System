from typing import Iterable, List
from unittest import TestCase

import numpy
import pytest
from worldpop_client.model.geo_json import GeoJson
from worldpop_client.model.geo_json_features import GeoJsonFeatures
from worldpop_client.model.geometry_object import GeometryObject

from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import Point, move_distance


class CircleToGeoJsonConverter:
    def __init__(self, area: AreaCircle, number_of_points: int):
        self._area = area
        self._number_of_points = number_of_points

    def convert(self) -> GeoJson:
        return GeoJson(
            features=[
                GeoJsonFeatures(
                    geometry=GeometryObject(
                        coordinates=self._coordinates
                    )
                )
            ]
        )

    @property
    def _coordinates(self) -> List[List[float]]:
        return [self._get_point(bearing=bearing) for bearing in self._bearings]

    def _get_point(self, bearing: float) -> List[float]:
        point = move_distance(bearing=bearing, kilometers=self._area.radius_in_kilometers, origin=self._area.center_coordinates)
        return [point.latitude, point.longitude]

    @property
    def _bearings(self) -> Iterable[float]:
        step_size = 360 / self._number_of_points
        return (i * step_size for i in range(self._number_of_points))


class TestCircleToGeoJson:
    _radius_in_kilometers = 150
    _number_of_points = 2
    _center = Point(latitude=0, longitude=0)

    def test(self):
        assert numpy.allclose(self._coordinates, self._expected_coordinates)

    @property
    def _coordinates(self) -> List[List[float]]:
        return self._geojson.features[0].geometry.coordinates

    @property
    def _geojson(self) -> GeoJson:
        return self._circle_to_geojson_converter.convert()

    @property
    def _expected_coordinates(self) -> List[List[float]]:
        return [[1.3565516705216198, 0.0], [-1.3565516705216198, 0]]

    @property
    def _circle_to_geojson_converter(self) -> CircleToGeoJsonConverter:
        return CircleToGeoJsonConverter(area=self._area, number_of_points=self._number_of_points)

    @property
    def _area(self) -> AreaCircle:
        return AreaCircle(
            center_coordinates=self._center,
            radius_in_kilometers=self._radius_in_kilometers
        )
