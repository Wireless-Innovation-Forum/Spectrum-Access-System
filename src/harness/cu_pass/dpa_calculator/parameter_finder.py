import logging
from dataclasses import dataclass
from statistics import mean
from typing import Callable

from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger


@dataclass
class InputWithReturnedValue:
    input: int
    returned_value: float

    def log(self) -> None:
        logger = get_dpa_calculator_logger()
        logger.info('\tFound parameter')
        logger.info(f'\t\tInput: {self.input}')
        logger.info(f'\t\tValue: {self.returned_value}\n')


class ParameterFinder:
    def __init__(self, function: Callable[[int], float], target: float, max_parameter: int = 500, step_size: int = 1):
        self._function = function
        self._step_size = step_size
        self._target = target

        self._min = 0
        self._max = self._initial_max = self._get_initial_max(max_parameter=max_parameter)

    def _get_initial_max(self, max_parameter: int) -> int:
        is_partial_step = bool(max_parameter % self._step_size)
        additional_step_if_necessary = self._step_size * is_partial_step
        return self._get_nearest_step_below(exact_input=max_parameter) + (additional_step_if_necessary)

    def find(self) -> InputWithReturnedValue:
        return self._perform_binary_search()

    def _perform_binary_search(self) -> InputWithReturnedValue:
        current_results = self._function_result_with_current_parameter()
        while self._input_found(current_results=current_results) is None:
            if self._target < current_results:
                self._min = self._current_parameter + self._step_size
            elif self._target > current_results:
                self._max = self._current_parameter - self._step_size
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
        exact_parameter = int(mean([self._min, self._max]))
        return self._get_nearest_step_below(exact_parameter)

    def _get_nearest_step_below(self, exact_input: int) -> int:
        return (exact_input // self._step_size) * self._step_size
