import random

import numpy
from behave import *

from testcases.cu_pass.dpa_calculator.features.environment.hooks import ContextSas

use_step_matcher("parse")


@given("random seed {seed:Integer}")
def step_impl(context: ContextSas, seed: int):
    random.seed(seed)
    numpy.random.seed(seed)
