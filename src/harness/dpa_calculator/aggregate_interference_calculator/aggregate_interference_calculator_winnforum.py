from dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator


class AggregateInterferenceCalculatorWinnforum(AggregateInterferenceCalculator):
    def calculate(self) -> float:
        self._set_dpa_neighbors()
        return self._dpa.CalcKeepListInterference(channel=self._first_inband_channel)[0]

    def _set_dpa_neighbors(self) -> None:
        self._dpa.nbor_lists = [set(self._grants_with_inband_frequences) for _ in self._dpa.nbor_lists]
