from geopy import Point
from geopy.distance import geodesic


def get_hat_creek_radio_observatory() -> Point:
    return Point(latitude=40.81734, longitude=-121.46933)


def move_distance(bearing: float, kilometers: float, origin: Point) -> Point:
    return geodesic(kilometers=kilometers).destination(point=origin, bearing=bearing)


if __name__ == '__main__':
    origin = get_hat_creek_radio_observatory()
    print(move_distance(bearing=180, kilometers=80, origin=origin).format_decimal(altitude=False))
