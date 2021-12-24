import sys
from typing import List
from unittest import mock

import boto3
from behave import *
from moto import mock_s3

from cu_pass.dpa_calculator import main as dpa_calculator_main

from testcases.cu_pass.features.environment.hooks import record_exception_if_expected
from testcases.cu_pass.features.helpers.utilities import delete_file
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


@fixture
def _clean_local_output_files(context: ContextDocker) -> None:
    yield
    delete_file(filepath=context.local_filepath_log)
    delete_file(filepath=context.local_filepath_result)


@fixture
def _mock_s3(context: ContextDocker) -> None:
    with mock_s3():
        yield


@when("the main docker command is run")
def step_impl(context: ContextDocker):
    with record_exception_if_expected(context=context):
        _setup_fixtures(context=context)
        if context.precreate_bucket:
            _create_bucket(context=context)
        _run_docker_command(context=context)


def _create_bucket(context: ContextDocker) -> None:
    s3_client = boto3.client('s3')
    s3_client.create_bucket(Bucket=context.s3_bucket,
                            CreateBucketConfiguration={'LocationConstraint': s3_client.meta.region_name})


def _setup_fixtures(context: ContextDocker) -> None:
    use_fixture(_clean_local_output_files, context=context)
    use_fixture(_mock_s3, context=context)


def _run_docker_command(context: ContextDocker) -> None:
    all_args = _get_args(context=context)
    with mock.patch.object(dpa_calculator_main, "__name__", "__main__"):
        with mock.patch.object(sys, 'argv', sys.argv + all_args):
            dpa_calculator_main.init()


def _get_args(context: ContextDocker) -> List[str]:
    dpa_name_arg = ['--dpa-name', context.dpa_name]
    local_filepath_log_arg = ['--local-log', context.local_filepath_log] if context.local_filepath_log else []
    local_filepath_result_arg = ['--local-result', context.local_filepath_result] if context.local_filepath_result else []
    number_of_iterations_arg = ['--iterations', str(context.number_of_iterations)]
    radius_arg = ['--radius', str(context.simulation_area_radius)]
    s3_bucket_arg = ['--s3-bucket', context.s3_bucket]
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
