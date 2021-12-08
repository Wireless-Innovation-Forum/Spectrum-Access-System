import random

from behave import *

from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher("parse")


@given("random seed {seed:Integer}")
def step_impl(context: ContextSas, seed: int):
    random.seed(seed)
