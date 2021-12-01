from dpa_calculator.population_retriever.population_retriever import PopulationRetriever


class PopulationRetrieverStraightFile(PopulationRetriever):
    def retrieve(self) -> int:
        mckinney_population = 1331000
        return mckinney_population
