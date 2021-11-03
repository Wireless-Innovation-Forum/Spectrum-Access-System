from shapely import geometry

from reference_models.geo.vincenty import GeodesicPoint


class Point:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return geometry.Point(self.latitude, self.longitude) == geometry.Point(other.latitude, other.longitude)

    @classmethod
    def from_shapely(cls, point_shapely: geometry.Point):
        return cls(latitude=point_shapely.y, longitude=point_shapely.x)


def get_hat_creek_radio_observatory() -> Point:
    return Point(latitude=40.81734, longitude=-121.46933)


def move_distance(bearing: float, kilometers: float, origin: Point) -> Point:
    latitude, longitude, _ = GeodesicPoint(lat=origin.latitude, lon=origin.longitude, dist_km=kilometers, bearing=bearing)
    return Point(latitude=latitude, longitude=longitude)
