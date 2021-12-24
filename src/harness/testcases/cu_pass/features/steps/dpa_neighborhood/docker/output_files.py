import glob
import json
from pathlib import Path

from behave import *

from cu_pass.dpa_calculator.main_runner.results_recorder import LOG_EXTENSION, LOG_PREFIX, RESULTS_EXTENSION, \
    RESULTS_PREFIX
from testcases.cu_pass.features.helpers.utilities import read_file, sanitize_output_log
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.expected_outputs.expected_log_output import \
    EXPECTED_LOG_OUTPUT
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.expected_outputs.expected_results_output import \
    EXPECTED_RESULTS_OUTPUT
from testcases.cu_pass.features.steps.dpa_neighborhood.docker.utilities import get_filepath_with_any_runtime, \
    get_s3_uploaded_filenames, \
    get_uploaded_file_content
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


NONE_STR = 'None'
SHOULD_STR = 'should'


@given("{s3_object_directory} as an s3 object directory name for s3 output")
def step_impl(context: ContextDocker, s3_object_directory: str):
    context.s3_output_directory = None if s3_object_directory == NONE_STR else s3_object_directory


@given("{local_filepath} as a local directory for local output")
def step_impl(context: ContextDocker, local_filepath: str):
    context.local_output_directory = None if local_filepath == NONE_STR else local_filepath


@then("the log file uploaded to S3 {should_exist_str} exist at {expected_s3_object_name}")
def step_impl(context: ContextDocker, should_exist_str: str, expected_s3_object_name: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_LOG_OUTPUT
        output_content = get_uploaded_file_content(bucket_name=context.s3_bucket, object_name=expected_s3_object_name)
        assert output_content == expected_content
    else:
        assert not _s3_file_exists(bucket_name=context.s3_bucket, partial_filename=LOG_EXTENSION), 'The log should not have been uploaded to s3'


@then("the local log file {should_exist_str} exist at {expected_filepath}")
def step_impl(context: ContextDocker, should_exist_str: bool, expected_filepath: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_LOG_OUTPUT
        local_content = _get_local_log_content(filepath=expected_filepath)
        assert local_content == expected_content
    else:
        assert not _local_file_exists(prefix=LOG_PREFIX, extension=LOG_EXTENSION)


def _get_local_log_content(filepath: str) -> str:
    found_filepath = get_filepath_with_any_runtime(filepath=filepath)
    return sanitize_output_log(log_filepath=found_filepath)


@then("the results file uploaded to S3 {should_exist_str} exist at {expected_s3_object_name}")
def step_impl(context: ContextDocker, should_exist_str: str, expected_s3_object_name: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_RESULTS_OUTPUT
        output_content = _get_uploaded_result_content(bucket_name=context.s3_bucket, object_name=expected_s3_object_name)
        assert output_content == expected_content, f'{output_content} != {expected_content}'
    else:
        assert not _s3_file_exists(bucket_name=context.s3_bucket, partial_filename=RESULTS_EXTENSION), 'The results should not have been uploaded to s3'


def _get_uploaded_result_content(bucket_name: str, object_name: str) -> str:
    content = get_uploaded_file_content(bucket_name=bucket_name, object_name=object_name)
    return _remove_runtime_from_results_content(content=content)


def _s3_file_exists(bucket_name: str, partial_filename: str) -> bool:
    uploaded_filenames = get_s3_uploaded_filenames(bucket_name=bucket_name)
    return any(partial_filename in filename for filename in uploaded_filenames)


@then("the local results file {should_exist_str} exist at {expected_filepath}")
def step_impl(context: ContextDocker, should_exist_str: str, expected_filepath: str):
    should_exist = should_exist_str == SHOULD_STR
    if should_exist:
        expected_content = EXPECTED_RESULTS_OUTPUT
        local_content = _get_local_result_content(filepath=expected_filepath)
        assert local_content == expected_content, f'{local_content} != {expected_content}'
    else:
        assert not _local_file_exists(prefix=RESULTS_PREFIX, extension=RESULTS_EXTENSION)


def _get_local_result_content(filepath: str) -> str:
    found_filepath = get_filepath_with_any_runtime(filepath=filepath)
    content = read_file(filepath=found_filepath)
    return _remove_runtime_from_results_content(content=content)


def _remove_runtime_from_results_content(content: str) -> str:
    dictionary = json.loads(content)
    dictionary['runtime'] = None
    return json.dumps(dictionary)


def _local_file_exists(prefix: str, extension: str) -> bool:
    output_log_paths = Path('**', f'{prefix}*{extension}')
    found_logs = glob.glob(str(output_log_paths), recursive=True)
    return bool(found_logs)
