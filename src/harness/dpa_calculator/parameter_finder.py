from statistics import mean
from typing import Awaitable, Callable, Optional


class ParameterFinder:
    def __init__(self, function: Callable[[int], Awaitable[float]], target: int, max_parameter: int = 20000):
        self._function = function
        self._target = target
        self._max_parameter = max_parameter

        self._min = 0
        self._max = 1

    async def find(self) -> int:
        results_extremity = await self._results_extremity()
        if results_extremity is not None:
            return results_extremity
        await self._grow_max_input()
        return await self._perform_binary_search()

    async def _results_extremity(self) -> Optional[int]:
        min_result = await self._function(self._max_parameter)
        if self._target < min_result:
            return self._max_parameter
        if self._target > await self._function(self._min):
            return self._min

    async def _grow_max_input(self) -> None:
        phase_one_counter = -1
        while self._target < await self._function_result_with_current_parameter():
            phase_one_counter += 1
            self._min = self._current_parameter
            self._max = self._min + 2 ** phase_one_counter

    async def _perform_binary_search(self) -> int:
        current_results = await self._function_result_with_current_parameter()
        while self._input_found(current_results=current_results) is None:
            if self._target < current_results:
                self._min = self._current_parameter + 1
            elif self._target > current_results:
                self._max = self._current_parameter - 1
            current_results = await self._function_result_with_current_parameter()
        return self._input_found(current_results=current_results)

    def _input_found(self, current_results: float) -> int:
        if self._min > self._max:
            return self._min
        if current_results == self._target:
            return self._current_parameter

    async def _function_result_with_current_parameter(self) -> float:
        return await self._function(self._current_parameter)

    @property
    def _current_parameter(self) -> int:
        return int(mean([self._min, self._max]))
