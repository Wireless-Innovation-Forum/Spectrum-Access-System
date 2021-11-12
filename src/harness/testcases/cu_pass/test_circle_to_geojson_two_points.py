from typing import List

from testcases.cu_pass.circle_to_geojson_tester import CircleToGeoJsonTester


class TestCircleToGeoJsonTwoPoints(CircleToGeoJsonTester):
    @property
    def _expected_coordinates(self) -> List[List[float]]:
        return [
            [self._north_coordinate, self._area.center_coordinates.longitude],
            [self._south_coordinate, self._area.center_coordinates.longitude]
        ]

    @property
    def _number_of_points(self) -> int:
        return 2
