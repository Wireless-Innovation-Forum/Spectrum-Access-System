from math import pi
from typing import Iterable, List, Optional

from worldpop_client.model.geo_json import GeoJson
from worldpop_client.model.geo_json_features import GeoJsonFeatures
from worldpop_client.model.geometry_object import GeometryObject

from dpa_calculator.point_distributor import AreaCircle
from dpa_calculator.utils import move_distance

DEGREES_IN_A_CIRCLE = 360


class CircleToGeoJsonConverter:
    def __init__(self, area: AreaCircle, number_of_points: Optional[int] = 150):
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
        unclosed_line = [self._get_point(bearing=bearing) for bearing in self._bearings]
        return unclosed_line + [unclosed_line[0]]

    def _get_point(self, bearing: float) -> List[float]:
        point = move_distance(bearing=bearing, kilometers=self._area.radius_in_kilometers, origin=self._area.center_coordinates)
        return [point.latitude, point.longitude]

    @property
    def _bearings(self) -> Iterable[float]:
        step_size = DEGREES_IN_A_CIRCLE / self._number_of_points
        return (i * step_size for i in range(self._number_of_points))
