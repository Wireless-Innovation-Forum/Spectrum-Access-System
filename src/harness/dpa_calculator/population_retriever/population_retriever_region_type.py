from dpa_calculator.constants import REGION_TYPE_DENSE_URBAN, REGION_TYPE_RURAL, REGION_TYPE_SUBURBAN, REGION_TYPE_URBAN
from dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from dpa_calculator.utilities import get_region_type


REGION_TYPE_TO_POPULATION = {
    REGION_TYPE_DENSE_URBAN: 4715098,
    REGION_TYPE_RURAL: 653558,
    REGION_TYPE_SUBURBAN: 1696558,
    REGION_TYPE_URBAN: 4715098
}


class PopulationRetrieverRegionType(PopulationRetriever):
    def retrieve(self) -> int:
        region_type = get_region_type(coordinates=self._area.center_coordinates)
        return REGION_TYPE_TO_POPULATION[region_type]
