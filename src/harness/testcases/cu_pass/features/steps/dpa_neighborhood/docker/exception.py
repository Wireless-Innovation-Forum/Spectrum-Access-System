import logging
from unittest import mock

from behave import *

from cu_pass.dpa_calculator.main_runner import main_runner
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger
from testcases.cu_pass.features.helpers.utilities import get_expected_output_content
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import get_uploaded_log_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

EXCEPTION_TEST_LOG_CONTENT = 'Test logs'

use_step_matcher("parse")


class ExceptionTest(Exception):
    pass


@fixture
def _exception_during_calculation(context: ContextDocker) -> None:
    def _exception_after_logs_are_written():
        logger = get_dpa_calculator_logger()
        logger.info(EXCEPTION_TEST_LOG_CONTENT)
        raise ExceptionTest
    with mock.patch.object(main_runner.AggregateInterferenceMonteCarloCalculator, 'simulate', side_effect=_exception_after_logs_are_written):
        yield


@given("an exception will be encountered during calculation")
def step_impl(context: ContextDocker):
    context.exception_expected = True
    use_fixture(_exception_during_calculation, context=context)


@then("the log file uploaded to S3 should be uploaded")
def step_impl(context: ContextDocker):
    expected_content = f'{EXCEPTION_TEST_LOG_CONTENT}\n'
    output_content = get_uploaded_log_content(bucket_name=context.s3_bucket)
    assert output_content == expected_content
