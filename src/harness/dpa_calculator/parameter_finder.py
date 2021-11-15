from statistics import mean
from typing import Callable, Optional


class ParameterFinder:
    def __init__(self, function: Callable[[int], float], target: int, max_parameter: int = 500):
        self._function = function
        self._target = target
        self._max_parameter = max_parameter

        self._min = 0
        self._max = 1

    def find(self) -> int:
        if self._results_extremity is not None:
            return self._results_extremity
        self._grow_max_input()
        return self._perform_binary_search()

    @property
    def _results_extremity(self) -> Optional[int]:
        if self._target < self._function(self._max_parameter):
            return self._max_parameter
        if self._target > self._function(self._min):
            return self._min

    def _grow_max_input(self) -> None:
        phase_one_counter = -1
        while self._target < self._function_result_with_current_parameter:
            phase_one_counter += 1
            self._min = self._current_parameter
            self._max = self._min + 2 ** phase_one_counter

    def _perform_binary_search(self) -> int:
        while self._input_found() is None:
            if self._target < self._function_result_with_current_parameter:
                self._min = self._current_parameter + 1
            elif self._target > self._function_result_with_current_parameter:
                self._max = self._current_parameter - 1
        return self._input_found()

    def _input_found(self) -> int:
        if self._min > self._max:
            return self._min
        if self._function_result_with_current_parameter == self._target:
            return self._current_parameter

    @property
    def _function_result_with_current_parameter(self) -> float:
        return self._function(self._current_parameter)

    @property
    def _current_parameter(self) -> int:
        return int(mean([self._min, self._max]))
