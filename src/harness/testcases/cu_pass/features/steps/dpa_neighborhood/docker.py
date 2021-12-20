import json
import sys
from pathlib import Path
from typing import List
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
ARBITRARY_NUMBER_OF_ITERATIONS = 1
ARBITRARY_OBJECT_NAME_LOG = 'arbitrary_object_name_log'
ARBITRARY_OBJECT_NAME_RESULT = 'arbitrary_object_name_result'


class ContextDocker(ContextSas):
    dpa_name: str
    iterations: int


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


@given("DPA name {dpa_name}")
def step_impl(context: ContextDocker, dpa_name: str):
    context.dpa_name = dpa_name


@given("{number_of_iterations:Integer} iterations")
def step_impl(context: ContextDocker, number_of_iterations: int):
    context.iterations = number_of_iterations


@given("an exception will be encountered during calculation")
def step_impl(context: ContextDocker):
    use_fixture(_exception_during_calculation, context=context)


@when("the main docker command is run")
def step_impl(context: ContextDocker):
    with record_exception(context=context):
        use_fixture(_mock_s3, context=context)
        all_args = _get_args(context=context)
        with mock.patch.object(dpa_calculator_main, "__name__", "__main__"):
            with mock.patch.object(sys, 'argv', sys.argv + all_args):
                dpa_calculator_main.init()


def _get_args(context: ContextDocker) -> List[str]:
    dpa_name_arg = ['--dpa-name', getattr(context, 'dpa_name', ARBITRARY_DPA_NAME)]
    number_of_iterations_arg = ['--iterations', str(getattr(context, 'iterations', ARBITRARY_NUMBER_OF_ITERATIONS))]
    s3_bucket_arg = ['--s3-bucket', ARBITRARY_BUCKET_NAME]
    s3_object_log_arg = ['--s3-object-log', ARBITRARY_OBJECT_NAME_LOG]
    s3_object_result_arg = ['--s3-object-result', ARBITRARY_OBJECT_NAME_RESULT]
    return dpa_name_arg \
           + number_of_iterations_arg \
           + s3_bucket_arg \
           + s3_object_log_arg \
           + s3_object_result_arg


@then("{expected_log_portion} should be in the output log")
def step_impl(context: ContextDocker, expected_log_portion: str):
    output_content = _get_uploaded_log_content()
    assert expected_log_portion in output_content


@then("the log file uploaded to S3 should be")
def step_impl(context: ContextDocker):
    expected_content = get_expected_output_content(context=context)
    output_content = _get_uploaded_log_content()
    assert output_content == expected_content


def _get_uploaded_log_content() -> str:
    return _get_uploaded_file_content(object_name=ARBITRARY_OBJECT_NAME_LOG)


@then("the results file uploaded to S3 should be")
def step_impl(context: ContextDocker):
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
