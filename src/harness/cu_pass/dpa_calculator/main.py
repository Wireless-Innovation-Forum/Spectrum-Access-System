import logging

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator
from cu_pass.dpa_calculator.dpa.builder import get_dpa


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    dpa = get_dpa(dpa_name='Hat Creek')
    results = AggregateInterferenceMonteCarloCalculator(dpa=dpa, number_of_iterations=2, simulation_area_radius_in_kilometers=100).simulate()
