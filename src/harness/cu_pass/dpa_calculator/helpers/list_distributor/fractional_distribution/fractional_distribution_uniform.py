from dataclasses import dataclass
from typing import List

import numpy
from scipy import stats

from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution


@dataclass
class FractionalDistributionUniform(FractionalDistribution):
    def assert_data_matches_distribution(self, data: List[float], leeway_fraction: float = 0.001) -> None:
        self._assert_data_range(data=data, leeway_fraction=leeway_fraction)
        self._assert_uniform_distribution(data=data)

    def _assert_uniform_distribution(self, data: List[float]) -> None:
        """
        https://stats.stackexchange.com/q/447941
        """
        data_within_range = self.get_data_within_range(data=data)
        if len(set(data_within_range)) > 1:
            comparable_distribution = numpy.random.uniform(self.range_minimum, self.range_maximum, len(data_within_range))
            statistic, critical_values, significance_level = stats.anderson_ksamp([comparable_distribution, data_within_range])
            assert statistic < critical_values[6], 'Data may not be normally distributed.'

    def get_values(self, number_of_values: int) -> List[float]:
        return numpy.random.uniform(self.range_minimum, self.range_maximum, number_of_values).tolist()

    def __str__(self) -> str:
        return f'{self.fraction * 100}%: {self.range_minimum}{f"-{self.range_maximum}" if self.range_minimum != self.range_maximum else ""}'
