import logging
from dataclasses import dataclass
from statistics import stdev
from typing import Callable, List, Tuple

import numpy
from numpy import asarray
from shapely import geometry

from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.geo.drive import nlcd_driver
from reference_models.geo.nlcd import LandCoverCodes
from reference_models.geo.vincenty import GeodesicDistanceBearing, GeodesicPoint


class Point:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return geometry.Point(self.latitude, self.longitude) == geometry.Point(other.latitude, other.longitude)

    @classmethod
    def from_shapely(cls, point_shapely: geometry.Point) -> 'Point':
        return cls(latitude=point_shapely.y, longitude=point_shapely.x)

    def to_shapely(self) -> geometry.Point:
        return geometry.Point(self.longitude, self.latitude)


def get_hat_creek_radio_observatory() -> Point:
    return Point(latitude=40.81734, longitude=-121.46933)


def move_distance(bearing: float, kilometers: float, origin: Point) -> Point:
    latitude, longitude, _ = GeodesicPoint(lat=origin.latitude, lon=origin.longitude, dist_km=kilometers, bearing=bearing)
    return Point(latitude=latitude, longitude=longitude)


def get_distance_between_two_points(point1: Point, point2: Point) -> float:
    return _get_geodesic_distance_bearing(point1=point1, point2=point2)[0]


def get_bearing_between_two_points(point1: Point, point2: Point) -> float:
    return _get_geodesic_distance_bearing(point1=point1, point2=point2)[1]


def _get_geodesic_distance_bearing(point1: Point, point2: Point) -> Tuple[float, float, float]:
    return GeodesicDistanceBearing(lat1=point1.latitude, lon1=point1.longitude, lat2=point2.latitude, lon2=point2.longitude)


def get_dpa_center(dpa: Dpa) -> Point:
    return Point.from_shapely(point_shapely=dpa.geometry.centroid)


def get_region_type(coordinates: Point) -> str:
    cbsd_region_code = nlcd_driver.GetLandCoverCodes(lat=coordinates.latitude, lon=coordinates.longitude)

    if cbsd_region_code == LandCoverCodes.DEVELOPED_LOW:
        return REGION_TYPE_SUBURBAN
    elif cbsd_region_code == LandCoverCodes.DEVELOPED_MEDIUM:
        return REGION_TYPE_URBAN
    elif cbsd_region_code == LandCoverCodes.DEVELOPED_HIGH:
        return REGION_TYPE_DENSE_URBAN

    return REGION_TYPE_RURAL


def region_is_rural(coordinates: Point) -> bool:
    return get_region_type(coordinates=coordinates) == REGION_TYPE_RURAL


@dataclass
class SimulationStatistics:
    percentile_50: float
    percentile_95: float
    maximum: float
    minimum: float
    standard_deviation: float
    title: str

    def log(self) -> None:
        logging.info(f'\nResults for {self.title}:')
        logging.info(f'\t50th percentile: {self.percentile_50}')
        logging.info(f'\t95th percentile: {self.percentile_95}')
        logging.info(f'\tStandard Deviation: {self.standard_deviation}')
        logging.info(f'\tMinimum: {self.minimum}')
        logging.info(f'\tMaximum: {self.maximum}')


def run_monte_carlo_simulation(functions_to_run: List[Callable[[], float]], number_of_iterations: int, percentile: int = 50) -> List[float]:
    results = []
    for i in range(number_of_iterations):
        logging.info(f'Monte Carlo iteration {i + 1}')
        iteration_results = [function_to_run() for function_to_run in functions_to_run]
        results.append(iteration_results)
    results_per_function = asarray(results).transpose()
    _log_results(results=results_per_function)
    return [_get_percentile(results=iteration_results, percentile=percentile) for iteration_results in results_per_function]


def _log_results(results: numpy.ndarray) -> None:
    simulation_statistics = [SimulationStatistics(
        percentile_50=_get_percentile(results=iteration_results, percentile=50),
        percentile_95=_get_percentile(results=iteration_results, percentile=95),
        maximum=max(iteration_results),
        minimum=min(iteration_results),
        standard_deviation=stdev(iteration_results),
        title='UEs' if index else 'APs'
    )
        for index, iteration_results in enumerate(results.tolist())]
    for statistics in simulation_statistics:
        statistics.log()


def _get_percentile(results: List[float], percentile: int) -> float:
    return numpy.percentile(results, percentile, interpolation='lower')

