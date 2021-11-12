from typing import List

from testcases.cu_pass.circle_to_geojson.circle_to_geojson_tester import CircleToGeoJsonTester


class TestCircleToGeoJsonTwoPoints(CircleToGeoJsonTester):
    @property
    def _expected_coordinates(self) -> List[List[float]]:
        start_point = [self._area.center_coordinates.longitude, self._north_coordinate]
        return [
            start_point,
            [self._area.center_coordinates.longitude, self._south_coordinate],
            start_point
        ]

    @property
    def _number_of_points(self) -> int:
        return 2
