from dataclasses import dataclass

from behave import *

from reference_models.dpa.dpa_mgr import Dpa
from testcases.cu_pass.features.environment.hooks import ContextSas


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
