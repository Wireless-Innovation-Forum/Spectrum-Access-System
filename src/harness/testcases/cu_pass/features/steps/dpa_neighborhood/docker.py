import json
import sys
from pathlib import Path
from unittest import mock

import boto3
from behave import *
from moto import mock_s3

from cu_pass.dpa_calculator import main as dpa_calculator_main
from cu_pass.dpa_calculator.dpa.builder import RadioAstronomyFacilityNames

from testcases.cu_pass.features.environment.hooks import ContextSas, record_exception
from testcases.cu_pass.features.environment.utilities import get_expected_output_content, sanitize_output_log

use_step_matcher("parse")


ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_DPA_NAME = RadioAstronomyFacilityNames.HatCreek.value
ARBITRARY_OBJECT_NAME_LOG = 'arbitrary_object_name_log'
ARBITRARY_OBJECT_NAME_RESULT = 'arbitrary_object_name_result'


class ExceptionTest(Exception):
    pass


@fixture
def _mock_s3(context: ContextSas) -> None:
    with mock_s3():
        yield


@fixture
def _exception_during_calculation(context: ContextSas) -> None:
    with mock.patch.object(dpa_calculator_main.AggregateInterferenceMonteCarloCalculator, 'simulate', side_effect=ExceptionTest):
        yield


@given("an exception will be encountered during calculation")
def step_impl(context: ContextSas):
    use_fixture(_exception_during_calculation, context=context)


@when("the main docker command is run")
def step_impl(context: ContextSas):
    with record_exception(context=context):
        use_fixture(_mock_s3, context=context)
        dpa_name_args = ['--dpa-name', ARBITRARY_DPA_NAME]
        s3_bucket_args = ['--s3-bucket', ARBITRARY_BUCKET_NAME]
        s3_object_log_args = ['--s3-object-log', ARBITRARY_OBJECT_NAME_LOG]
        s3_object_result_args = ['--s3-object-result', ARBITRARY_OBJECT_NAME_RESULT]
        all_args = dpa_name_args + s3_bucket_args + s3_object_log_args + s3_object_result_args
        with mock.patch.object(dpa_calculator_main, "__name__", "__main__"):
            with mock.patch.object(sys, 'argv', sys.argv + all_args):
                dpa_calculator_main.init()


@then("the log file uploaded to S3 should be")
def step_impl(context: ContextSas):
    expected_content = get_expected_output_content(context=context)
    output_content = _get_uploaded_log_content()
    assert output_content == expected_content, f'{output_content} != {expected_content}'


def _get_uploaded_log_content() -> str:
    return _get_uploaded_file_content(object_name=ARBITRARY_OBJECT_NAME_LOG)


@then("the results file uploaded to S3 should be")
def step_impl(context: ContextSas):
    expected_content = get_expected_output_content(context=context)
    output_content = _get_uploaded_result_content()
    assert output_content == expected_content, f'{output_content} != {expected_content}'


def _get_uploaded_result_content() -> str:
    content = _get_uploaded_file_content(object_name=ARBITRARY_OBJECT_NAME_RESULT)
    dictionary = json.loads(content)
    dictionary['runtime'] = None
    return json.dumps(dictionary)


def _get_uploaded_file_content(object_name: str) -> str:
    s3 = boto3.client('s3')
    uploaded_file_local_filepath = 'tmp'
    try:
        s3.download_file(ARBITRARY_BUCKET_NAME, object_name, uploaded_file_local_filepath)
        output_content = sanitize_output_log(log_filepath=uploaded_file_local_filepath)
    finally:
        Path(uploaded_file_local_filepath).unlink()
    return output_content
