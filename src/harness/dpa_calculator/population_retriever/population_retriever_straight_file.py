from os import getenv

import numpy
from dotenv import load_dotenv
from shapely import geometry

from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from reference_models.geo.utils import GridPolygon
from reference_models.geo.zones import GetUsBorder
from src.lib.geo import geo_utils
from src.lib.usgs_pop.usgs_pop_driver import UsgsPopDriver


class PopulationRetrieverStraightFile(PopulationRetriever):
    async def retrieve(self) -> int:
        mckinney_population = 1331000
        return mckinney_population
