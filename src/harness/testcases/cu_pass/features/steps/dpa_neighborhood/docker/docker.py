import json
import logging
import sys
from pathlib import Path
from typing import List
from unittest import mock

import boto3
from behave import *
from moto import mock_s3

from cu_pass.dpa_calculator import main as dpa_calculator_main
from cu_pass.dpa_calculator.main import LOG_EXTENSION

from testcases.cu_pass.features.environment.hooks import ContextSas, record_exception
from testcases.cu_pass.features.environment.utilities import get_expected_output_content, sanitize_output_log
from testcases.cu_pass.features.helpers.utilities import read_file
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.expected_log_output import EXPECTED_LOG_OUTPUT
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")

ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'


class ExceptionTest(Exception):
    pass


@fixture
def _clean_local_output_files(context: ContextDocker) -> None:
    yield
    _delete_file(filepath=context.local_filepath_log)
    _delete_file(filepath=context.local_filepath_result)


def _delete_file(filepath: str) -> None:
    try:
        Path(filepath).unlink()
    except FileNotFoundError:
        pass


@fixture
def _mock_s3(context: ContextDocker) -> None:
    with mock_s3():
        yield


@fixture
def _exception_during_calculation(context: ContextSas) -> None:
    def _exception_after_logs_are_written():
        logging.info('Test logs')
        raise ExceptionTest
    with mock.patch.object(dpa_calculator_main.AggregateInterferenceMonteCarloCalculator, 'simulate', side_effect=_exception_after_logs_are_written):
        yield


@given("DPA name {dpa_name}")
def step_impl(context: ContextDocker, dpa_name: str):
    context.dpa_name = dpa_name


@given("an exception will be encountered during calculation")
def step_impl(context: ContextDocker):
    context.exception_expected = True
    use_fixture(_exception_during_calculation, context=context)


@given("{s3_object_name} as an s3 object name for the s3 log file")
def step_impl(context: ContextDocker, s3_object_name: str):
    context.s3_object_name_log = None if s3_object_name == 'None' else s3_object_name


@given("{local_filepath} as a local filepath for the local log file")
def step_impl(context: ContextDocker, local_filepath: str):
    context.local_filepath_log = local_filepath


@given("{s3_object_name} as an s3 object name for the s3 results file")
def step_impl(context: ContextDocker, s3_object_name: str):
    context.s3_object_name_result = s3_object_name


@given("{local_filepath} as a local filepath for the local results file")
def step_impl(context: ContextDocker, local_filepath: str):
    context.local_filepath_result = local_filepath


@when("the main docker command is run")
def step_impl(context: ContextDocker):
    def main():
        use_fixture(_clean_local_output_files, context=context)
        use_fixture(_mock_s3, context=context)
        all_args = _get_args(context=context)
        with mock.patch.object(dpa_calculator_main, "__name__", "__main__"):
            with mock.patch.object(sys, 'argv', sys.argv + all_args):
                dpa_calculator_main.init()

    if context.exception_expected:
        with record_exception(context=context):
            main()
    else:
        main()


def _get_args(context: ContextDocker) -> List[str]:
    dpa_name_arg = ['--dpa-name', context.dpa_name]
    local_filepath_log_arg = ['--local-log', context.local_filepath_log] if context.local_filepath_log else []
    local_filepath_result_arg = ['--local-result', context.local_filepath_result] if context.local_filepath_result else []
    number_of_iterations_arg = ['--iterations', str(context.number_of_iterations)]
    radius_arg = ['--radius', str(context.simulation_area_radius)]
    s3_bucket_arg = ['--s3-bucket', ARBITRARY_BUCKET_NAME]
    s3_object_log_arg = ['--s3-object-log', context.s3_object_name_log] if context.s3_object_name_log else []
    s3_object_result_arg = ['--s3-object-result', context.s3_object_name_result] if context.s3_object_name_result else []

    return dpa_name_arg \
        + local_filepath_log_arg \
        + local_filepath_result_arg \
        + number_of_iterations_arg \
        + radius_arg \
        + s3_bucket_arg \
        + s3_object_log_arg \
        + s3_object_result_arg


@then("{expected_log_portion} should be in the output log")
def step_impl(context: ContextDocker, expected_log_portion: str):
    output_content = _get_uploaded_log_content(context=context)
    assert expected_log_portion in output_content


@then("the log file uploaded to S3 {should_exist_str} exist")
def step_impl(context: ContextDocker, should_exist_str: str):
    should_exist = should_exist_str == 'should'
    if should_exist:
        expected_content = EXPECTED_LOG_OUTPUT
        output_content = _get_uploaded_log_content(context=context)
        assert output_content == expected_content
    else:
        s3 = boto3.client('s3')
        uploaded_contents = s3.list_objects(Bucket=ARBITRARY_BUCKET_NAME)['Contents']
        uploaded_filenames = [key['Key'] for key in uploaded_contents]
        log_file_has_been_uploaded = any(LOG_EXTENSION in filename for filename in uploaded_filenames)
        assert not log_file_has_been_uploaded, 'The log should not have been uploaded to s3'


@then("the local log file should exist")
def step_impl(context: ContextDocker):
    expected_content = EXPECTED_LOG_OUTPUT
    local_content = _get_local_log_content(context=context)
    assert local_content == expected_content


def _get_uploaded_log_content(context: ContextDocker) -> str:
    return _get_uploaded_file_content(object_name=context.s3_object_name_log)


def _get_local_log_content(context: ContextDocker) -> str:
    filepath = context.local_filepath_log
    return sanitize_output_log(log_filepath=filepath)


@then("the results file uploaded to S3 should be")
def step_impl(context: ContextDocker):
    expected_content = get_expected_output_content(context=context)
    output_content = _get_uploaded_result_content(context=context)
    assert output_content == expected_content, f'{output_content} != {expected_content}'


@then("the local results file should match the s3 results file")
def step_impl(context: ContextDocker):
    s3_content = _get_uploaded_result_content(context=context)
    local_content = _get_local_result_content(context=context)
    assert local_content == s3_content, f'{local_content} != {s3_content}'


def _get_uploaded_result_content(context: ContextDocker) -> str:
    content = _get_uploaded_file_content(object_name=context.s3_object_name_result)
    return _remove_runtime_from_results_content(content=content)


def _get_uploaded_file_content(object_name: str) -> str:
    s3 = boto3.client('s3')
    uploaded_file_local_filepath = 'tmp'
    try:
        s3.download_file(ARBITRARY_BUCKET_NAME, object_name, uploaded_file_local_filepath)
        output_content = sanitize_output_log(log_filepath=uploaded_file_local_filepath)
    finally:
        _delete_file(filepath=uploaded_file_local_filepath)
    return output_content


def _get_local_result_content(context: ContextDocker) -> str:
    content = read_file(filepath=context.local_filepath_result)
    return _remove_runtime_from_results_content(content=content)


def _remove_runtime_from_results_content(content: str) -> str:
    dictionary = json.loads(content)
    dictionary['runtime'] = None
    return json.dumps(dictionary)
