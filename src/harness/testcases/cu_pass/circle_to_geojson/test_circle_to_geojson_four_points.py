from typing import List

from testcases.cu_pass.circle_to_geojson.circle_to_geojson_tester import CircleToGeoJsonTester


class TestCircleToGeoJsonFourPoints(CircleToGeoJsonTester):
    _east_coordinate = 1.347472926179282

    @property
    def _expected_coordinates(self) -> List[List[float]]:
        start_point = [self._north_coordinate, self._area.center_coordinates.longitude]
        return [
            start_point,
            [self._area.center_coordinates.latitude, self._east_coordinate],
            [self._south_coordinate, self._area.center_coordinates.longitude],
            [self._area.center_coordinates.latitude, self._west_coordiante],
            start_point
        ]

    @property
    def _west_coordiante(self) -> float:
        return -self._east_coordinate

    @property
    def _number_of_points(self) -> int:
        return 4
