import glob
import json
from pathlib import Path

import boto3
from behave import *

from cu_pass.dpa_calculator.main import LOG_EXTENSION, LOG_PREFIX, RESULTS_EXTENSION, RESULTS_PREFIX
from testcases.cu_pass.features.helpers.utilities import read_file, sanitize_output_log
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.expected_outputs.expected_log_output import \
    EXPECTED_LOG_OUTPUT
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.expected_outputs.expected_results_output import \
    EXPECTED_RESULTS_OUTPUT
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import ARBITRARY_BUCKET_NAME, \
    get_uploaded_file_content, get_uploaded_log_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


NONE_STR = 'None'
SHOULD_STR = 'should'


@given("{s3_object_name} as an s3 object name for the s3 log file")
def step_impl(context: ContextDocker, s3_object_name: str):
    context.s3_object_name_log = None if s3_object_name == NONE_STR else s3_object_name


@given("{local_filepath} as a local filepath for the local log file")
def step_impl(context: ContextDocker, local_filepath: str):
    context.local_filepath_log = None if local_filepath == NONE_STR else local_filepath


@given("{s3_object_name} as an s3 object name for the s3 results file")
def step_impl(context: ContextDocker, s3_object_name: str):
    context.s3_object_name_result = None if s3_object_name == NONE_STR else s3_object_name


@given("{local_filepath} as a local filepath for the local results file")
def step_impl(context: ContextDocker, local_filepath: str):
    context.local_filepath_result = None if local_filepath == NONE_STR else local_filepath


@then("the log file uploaded to S3 {should_exist_str} exist")
def step_impl(context: ContextDocker, should_exist_str: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_LOG_OUTPUT
        output_content = get_uploaded_log_content(context=context)
        assert output_content == expected_content
    else:
        assert not _s3_file_exists(partial_filename=LOG_EXTENSION), 'The log should not have been uploaded to s3'


@then("the local log file {should_exist_str} exist")
def step_impl(context: ContextDocker, should_exist_str: bool):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_LOG_OUTPUT
        local_content = _get_local_log_content(context=context)
        assert local_content == expected_content
    else:
        assert not _local_file_exists(prefix=LOG_PREFIX, extension=LOG_EXTENSION)


def _get_local_log_content(context: ContextDocker) -> str:
    filepath = context.local_filepath_log
    return sanitize_output_log(log_filepath=filepath)


@then("the results file uploaded to S3 {should_exist_str} exist")
def step_impl(context: ContextDocker, should_exist_str: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_RESULTS_OUTPUT
        output_content = _get_uploaded_result_content(context=context)
        assert output_content == expected_content, f'{output_content} != {expected_content}'
    else:
        assert not _s3_file_exists(partial_filename=RESULTS_EXTENSION), 'The results should not have been uploaded to s3'


def _get_uploaded_result_content(context: ContextDocker) -> str:
    content = get_uploaded_file_content(object_name=context.s3_object_name_result)
    return _remove_runtime_from_results_content(content=content)


def _s3_file_exists(partial_filename: str) -> bool:
    s3 = boto3.client('s3')
    uploaded_contents = s3.list_objects(Bucket=ARBITRARY_BUCKET_NAME)['Contents']
    uploaded_filenames = [key['Key'] for key in uploaded_contents]
    return any(partial_filename in filename for filename in uploaded_filenames)


@then("the local results file {should_exist_str} exist")
def step_impl(context: ContextDocker, should_exist_str: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_RESULTS_OUTPUT
        local_content = _get_local_result_content(context=context)
        assert local_content == expected_content, f'{local_content} != {expected_content}'
    else:
        assert not _local_file_exists(prefix=RESULTS_PREFIX, extension=RESULTS_EXTENSION)


def _get_local_result_content(context: ContextDocker) -> str:
    content = read_file(filepath=context.local_filepath_result)
    return _remove_runtime_from_results_content(content=content)


def _remove_runtime_from_results_content(content: str) -> str:
    dictionary = json.loads(content)
    dictionary['runtime'] = None
    return json.dumps(dictionary)


def _local_file_exists(prefix: str, extension: str) -> bool:
    output_log_paths = Path('**', f'{prefix}*{extension}')
    found_logs = glob.glob(str(output_log_paths), recursive=True)
    return bool(found_logs)
