import json

from numpy import int64

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.aggregate_interference_monte_carlo_calculator import \
    ResultsEncoder


class TestResultsEncoder:
    def test_int64(self):
        obj = {'key': int64(1)}
        json.dumps(obj, cls=ResultsEncoder)
