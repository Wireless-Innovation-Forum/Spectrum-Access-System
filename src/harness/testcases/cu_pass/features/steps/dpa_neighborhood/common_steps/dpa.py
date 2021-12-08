from dataclasses import dataclass

from behave import *

from dpa_calculator.dpa.dpa import Dpa
from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher('parse')


@dataclass
class ContextDpa(ContextSas):
    dpa: Dpa


@given("an antenna at {dpa:Dpa}")
def step_impl(context: ContextDpa, dpa: Dpa):
    """
    Args:
        context (behave.runner.Context):
    """
    context.dpa = dpa
