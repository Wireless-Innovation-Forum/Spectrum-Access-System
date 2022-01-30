from typing import Optional

from cu_pass.dpa_calculator.binary_search.binary_search import BinarySearch, BinarySearchBoundaries


class ShortestUnchangingInputFinder(BinarySearch):
    @property
    def _input_found(self) -> Optional[int]:
        current_results = self._function_result_with_current_parameter()
        if self._min > self._max:
            return min(self._min, self._initial_max)
        elif self._one_input_lower_result() != current_results and self._max_input_result() == current_results:
            return self._current_parameter

    @property
    def _updated_boundaries(self) -> BinarySearchBoundaries:
        new_boundaries = BinarySearchBoundaries(maximum=self._max, minimum=self._min)
        current_results = self._function_result_with_current_parameter()

        if self._max_input_result() != current_results:
            new_boundaries.minimum = self._current_parameter + self._step_size
        elif self._one_input_lower_result() == current_results:
            new_boundaries.maximum = self._current_parameter - self._step_size

        return new_boundaries

    def _one_input_lower_result(self) -> float:
        lower_input = self._current_parameter - self._step_size
        return self._run_function(input=lower_input)

    def _max_input_result(self) -> float:
        return self._run_function(input=self._initial_max)
