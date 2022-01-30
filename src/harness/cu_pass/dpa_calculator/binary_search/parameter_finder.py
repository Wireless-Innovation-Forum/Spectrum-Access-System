from typing import Callable, Optional

from cu_pass.dpa_calculator.binary_search.binary_search import BinarySearch, BinarySearchBoundaries


class ParameterFinder(BinarySearch):
    def __init__(self, function: Callable[[int], float], target: float, max_parameter: int = 500, step_size: int = 1):
        super().__init__(function=function, max_parameter=max_parameter, step_size=step_size)
        self._target = target

    @property
    def _input_found(self) -> Optional[int]:
        if self._min > self._max:
            return min(self._min, self._initial_max)
        if self._function_result_with_current_parameter() == self._target:
            return self._current_parameter

    def _updated_boundaries(self) -> BinarySearchBoundaries:
        new_boundaries = BinarySearchBoundaries(maximum=self._max, minimum=self._min)
        current_results = self._function_result_with_current_parameter()

        if self._target < current_results:
            new_boundaries.minimum = self._current_parameter + self._step_size
        elif self._target > current_results:
            new_boundaries.maximum = self._current_parameter - self._step_size

        return new_boundaries
