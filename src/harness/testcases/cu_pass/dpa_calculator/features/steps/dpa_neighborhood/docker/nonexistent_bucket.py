from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker


@given("\"{bucket_name}\" as an s3 bucket name")
def step_impl(context: ContextDocker, bucket_name: str):
    context.s3_bucket = bucket_name


@given("the bucket does not already exist")
def step_impl(context: ContextDocker):
    context.exception_expected = True
    context.precreate_bucket = False


@then("an error message should say \"{expected_message}\"")
def step_impl(context: ContextDocker, expected_message: str):
    error_message = str(context.exception)
    assert error_message == expected_message, f'{error_message} != {expected_message}'
