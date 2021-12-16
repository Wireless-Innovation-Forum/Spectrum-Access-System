import random

from numpy import asarray, ndarray

DEGREES_IN_A_CIRCLE = 360
GAIN_PATTERN_DEFAULT_MINIMUM = 0
GAIN_PATTERN_DEFAULT_MAXIMUM = 6


def get_uniform_gain_pattern() -> ndarray:
    return asarray([random.uniform(GAIN_PATTERN_DEFAULT_MINIMUM, GAIN_PATTERN_DEFAULT_MAXIMUM) for _ in range(DEGREES_IN_A_CIRCLE)])
