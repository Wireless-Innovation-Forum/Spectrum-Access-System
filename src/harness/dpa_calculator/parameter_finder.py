from statistics import mean
from typing import Awaitable, Callable, Optional


class ParameterFinder:
    def __init__(self, function: Callable[[int], float], target: float, max_parameter: int = 500):
        self._function = function
        self._target = target

        self._min = 0
        self._max = max_parameter

    def find(self) -> int:
        return self._perform_binary_search()

    def _perform_binary_search(self) -> int:
        current_results = self._function_result_with_current_parameter()
        while self._input_found(current_results=current_results) is None:
            if self._target < current_results:
                self._min = self._current_parameter + 1
            elif self._target > current_results:
                self._max = self._current_parameter - 1
            current_results = self._function_result_with_current_parameter()
        return self._input_found(current_results=current_results)

    def _input_found(self, current_results: float) -> int:
        if self._min > self._max:
            return self._min
        if current_results == self._target:
            return self._current_parameter

    def _function_result_with_current_parameter(self) -> float:
        return self._function(self._current_parameter)

    @property
    def _current_parameter(self) -> int:
        return int(mean([self._min, self._max]))
