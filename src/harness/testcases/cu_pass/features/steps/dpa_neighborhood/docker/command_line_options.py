import re

from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import get_uploaded_log_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.parsers.parse_dpa import parse_dpa

use_step_matcher("parse")


@given("DPA name {dpa:Dpa}")
def step_impl(context: ContextDocker, dpa: str):
    context.dpa = dpa


@then("{expected_log_portion} should be in the output log")
def step_impl(context: ContextDocker, expected_log_portion: str):
    output_content = get_uploaded_log_content(bucket_name=context.s3_bucket)
    assert re.search(expected_log_portion, output_content)
