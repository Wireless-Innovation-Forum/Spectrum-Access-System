from os import getenv

import numpy
from dotenv import load_dotenv
from shapely import geometry

from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from reference_models.geo.utils import GridPolygon
from reference_models.geo.zones import GetUsBorder
from src.lib.geo import geo_utils
from src.lib.usgs_pop.usgs_pop_driver import UsgsPopDriver

load_dotenv()


POPULATION_DIRECTORY_CENSUS = getenv('POPULATION_DIRECTORY_CENSUS')


POPULATION_RESOLUTION_IN_ARCSECONDS = 10  # from src.studies.esc_impact_pop.esc_pop_impact


def ComputeSensorNeighborhood(latitude, longitude, radius_km, res_arcsec):
    """
    from src.studies.esc_impact_pop.esc_pop_impact
    """
    us_border = GetUsBorder()
    sensor_nbor = geo_utils.Buffer(geometry.Point(longitude, latitude), radius_km)
    sensor_nbor = sensor_nbor.intersection(us_border)
    longitudes, latitudes = list(zip(*GridPolygon(sensor_nbor, res_arcsec)))
    return latitudes, longitudes, sensor_nbor


class PopulationRetrieverCensus(PopulationRetriever):
    _resolution_in_arcseconds = POPULATION_RESOLUTION_IN_ARCSECONDS

    async def retrieve(self) -> int:
        popper = UsgsPopDriver(pop_directory=POPULATION_DIRECTORY_CENSUS, lazy_load=True)
        lats, lons, _ = ComputeSensorNeighborhood(latitude=self._area.center_coordinates.latitude,
                                                  longitude=self._area.center_coordinates.longitude,
                                                  radius_km=self._area.radius_in_kilometers,
                                                  res_arcsec=self._resolution_in_arcseconds)

        lats, lons = numpy.array(lats), numpy.array(lons)
        idxs = numpy.arange(len(lats))

        # Compute the standalone population impact for that sensor.
        return round(
                geo_utils.AreaPlateCarreePixel(res_arcsec=self._resolution_in_arcseconds,
                                               ref_latitude=self._area.center_coordinates.latitude) *
                numpy.sum(popper.GetPopulationDensity(lats[idxs], lons[idxs])))
