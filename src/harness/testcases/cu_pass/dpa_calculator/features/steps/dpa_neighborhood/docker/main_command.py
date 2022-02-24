import sys
from shutil import rmtree
from typing import List
from unittest import mock

import boto3
from behave import *
from moto import mock_s3

from cu_pass.dpa_calculator import main as dpa_calculator_main
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories

from testcases.cu_pass.dpa_calculator.features.environment.hooks import record_exception_if_expected
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_cbsd_deployment_options import \
    get_current_simulation_distances
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


@fixture
def _clean_local_output_files(context: ContextDocker) -> None:
    yield
    rmtree(context.local_output_directory, ignore_errors=True)


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
    simulation_distances = get_current_simulation_distances(context=context, default={})

    dpa_name_arg = ['--dpa-name', context.dpa.name]
    local_output_arg = ['--local-output-directory', context.local_output_directory] if context.local_output_directory else []
    number_of_iterations_arg = ['--iterations', str(context.number_of_iterations)]
    distance_category_a_arg = ['--category-a-radius', str(simulation_distances.get(CbsdCategories.A, 0))]
    distance_category_b_arg = ['--category-b-radius', str(simulation_distances.get(CbsdCategories.B, 0))]
    s3_bucket_arg = ['--s3-bucket', context.s3_bucket]
    s3_output_arg = ['--s3-output-directory', context.s3_output_directory] if context.s3_output_directory else []
    ue_runs_arg = ['--include-ue-runs'] if context.include_ue_runs else []
    neighborhood_categories_arg = context.neighborhood_categories and ['--neighborhood-category', context.neighborhood_categories[0].value]
    interference_threshold_arg = ['--interference-threshold', str(context.interference_threshold)] if context.interference_threshold is not None else []
    beamwidth_arg = ['--beamwidth', str(context.beamwidth)] if context.beamwidth is not None else []

    return dpa_name_arg \
        + local_output_arg \
        + number_of_iterations_arg \
        + distance_category_a_arg \
        + distance_category_b_arg \
        + s3_bucket_arg \
        + s3_output_arg \
        + ue_runs_arg \
        + neighborhood_categories_arg \
        + interference_threshold_arg \
        + beamwidth_arg
