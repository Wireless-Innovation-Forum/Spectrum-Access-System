from dataclasses import dataclass
from statistics import mean
from typing import Callable


@dataclass
class InputWithReturnedValue:
    input: int
    returned_value: float


class ParameterFinder:
    def __init__(self, function: Callable[[int], float], target: float, max_parameter: int = 500):
        self._function = function
        self._target = target

        self._min = 0
        self._max = self._initial_max = max_parameter

    def find(self) -> InputWithReturnedValue:
        return self._perform_binary_search()

    def _perform_binary_search(self) -> InputWithReturnedValue:
        current_results = self._function_result_with_current_parameter()
        while self._input_found(current_results=current_results) is None:
            if self._target < current_results:
                self._min = self._current_parameter + 1
            elif self._target > current_results:
                self._max = self._current_parameter - 1
            current_results = self._function_result_with_current_parameter()
        input_found = self._input_found(current_results=current_results)
        return InputWithReturnedValue(
            input=input_found,
            returned_value=self._function(input_found)
        )

    def _input_found(self, current_results: float) -> int:
        if self._min > self._max:
            return min(self._min, self._initial_max)
        if current_results == self._target:
            return self._current_parameter

    def _function_result_with_current_parameter(self) -> float:
        return self._function(self._current_parameter)

    @property
    def _current_parameter(self) -> int:
        return int(mean([self._min, self._max]))
