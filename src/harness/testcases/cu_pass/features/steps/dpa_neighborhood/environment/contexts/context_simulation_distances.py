from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    NEIGHBORHOOD_DISTANCES_TYPE
from testcases.cu_pass.features.environment.hooks import ContextSas


class ContextSimulationDistances(ContextSas):
    simulation_distances: NEIGHBORHOOD_DISTANCES_TYPE
