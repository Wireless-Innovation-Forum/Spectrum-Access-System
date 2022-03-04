from dataclasses import dataclass
from math import isclose
from statistics import mean, stdev
from typing import List

from scipy.stats import normaltest, truncnorm

from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution

DEFAULT_NULL_HYPOTHESIS_ALPHA = 1e-3


@dataclass
class FractionalDistributionNormal(FractionalDistribution):
    mean: float
    standard_deviation: float

    def get_values(self, number_of_values: int) -> List[float]:
        lower_bound = (self.range_minimum - self.mean) / self.standard_deviation
        upper_bound = (self.range_maximum - self.mean) / self.standard_deviation
        generator = truncnorm(lower_bound, upper_bound, loc=self.mean, scale=self.standard_deviation)
        return generator.rvs(number_of_values).tolist()

    def assert_data_matches_distribution(self,
                                         data: List[float],
                                         leeway_fraction: float = 0.001,
                                         leeyway_mean: float = 0.2,
                                         leeyway_standard_deviation: float = 0.2) -> None:
        self._assert_data_range(data=data, leeway_fraction=leeway_fraction)
        self._assert_normal_distribution(data=data,
                                         leeyway_mean=leeyway_mean,
                                         leeyway_standard_deviation=leeyway_standard_deviation)

    def _assert_normal_distribution(self,
                                    data: List[float],
                                    leeyway_mean: float,
                                    leeyway_standard_deviation: float) -> None:
        data_within_range = self.get_data_within_range(data=data)
        assert isclose(mean(data_within_range), self.mean, abs_tol=leeyway_mean), 'Mean does not match.'
        assert isclose(stdev(data_within_range), self.standard_deviation, abs_tol=leeyway_standard_deviation), 'Standard deviation does not match.'
        assert not self._can_reject_null_hypothesis_for_normal_distribution(data=data), 'Data may not be normally distributed.'

    def _can_reject_null_hypothesis_for_normal_distribution(self, data: List[float]) -> bool:
        """
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.normaltest.html
        """
        data_within_range = self.get_data_within_range(data=data)
        return normaltest(data_within_range)[1] < DEFAULT_NULL_HYPOTHESIS_ALPHA

    def __str__(self) -> str:
        return f'{self.fraction * 100}%: PDF [{self.range_minimum}-{self.range_maximum}] mean {self.mean} std {self.standard_deviation}'
