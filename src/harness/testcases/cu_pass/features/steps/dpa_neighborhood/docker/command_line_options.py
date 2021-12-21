from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import get_uploaded_log_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


@given("DPA name {dpa_name}")
def step_impl(context: ContextDocker, dpa_name: str):
    context.dpa_name = dpa_name


@then("{expected_log_portion} should be in the output log")
def step_impl(context: ContextDocker, expected_log_portion: str):
    output_content = get_uploaded_log_content(context=context)
    assert expected_log_portion in output_content
