from math import inf
from statistics import mean
from typing import Callable


class ParameterFinder:
    def __init__(self, function: Callable[[int], float], target: int, max_parameter: int = 500):
        self._function = function
        self._target = target
        self._min = 0
        self._max = 1
        self._max_parameter = max_parameter

    def find(self) -> int:
        result = inf
        in_phase_one = True
        phase_one_counter = 0
        while True:
            if self._target < self._function(self._max_parameter):
                return self._max_parameter
            if self._target > self._function(self._min):
                return self._min
            if self._min > self._max:
                return self._max
            if result == self._target:
                return self._current_parameter

            if self._target > result:
                in_phase_one = False

            if in_phase_one:
                self._min = self._current_parameter
                self._max = self._min + 2 ** phase_one_counter
                phase_one_counter += 1
            else:
                if self._target < result:
                    self._min = self._current_parameter + 1
                elif self._target > result:
                    self._max = self._current_parameter - 1
            result = self._function(self._current_parameter)

    @property
    def _current_parameter(self) -> int:
        return int(mean([self._min, self._max]))
