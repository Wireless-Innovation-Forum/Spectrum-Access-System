import logging
from unittest import mock

from behave import *

from cu_pass.dpa_calculator.main_runner import main_runner
from testcases.cu_pass.features.helpers.utilities import get_expected_output_content
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import get_uploaded_log_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


class ExceptionTest(Exception):
    pass


@fixture
def _exception_during_calculation(context: ContextDocker) -> None:
    def _exception_after_logs_are_written():
        logging.info('Test logs')
        raise ExceptionTest
    with mock.patch.object(main_runner.AggregateInterferenceMonteCarloCalculator, 'simulate', side_effect=_exception_after_logs_are_written):
        yield


@given("an exception will be encountered during calculation")
def step_impl(context: ContextDocker):
    context.exception_expected = True
    use_fixture(_exception_during_calculation, context=context)


@then("the log file uploaded to S3 should be")
def step_impl(context: ContextDocker):
    expected_content = get_expected_output_content(context=context)
    output_content = get_uploaded_log_content(bucket_name=context.s3_bucket)
    assert output_content == expected_content
