import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import boto3
from behave import *
from moto import mock_s3

from cu_pass.dpa_calculator import main as dpa_calculator_main
from cu_pass.dpa_calculator.dpa.builder import RadioAstronomyFacilityNames

from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher("parse")


ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_DPA_NAME = RadioAstronomyFacilityNames.HatCreek.value
ARBITRARY_OBJECT_NAME = 'arbitrary_object_name'


@fixture
def _mock_s3(context: ContextSas) -> None:
    with mock_s3():
        yield


@when("the main docker command is run")
def step_impl(context: ContextSas):
    use_fixture(_mock_s3, context=context)
    dpa_name_args = ['--dpa-name', ARBITRARY_DPA_NAME]
    s3_bucket_args = ['--s3-bucket', ARBITRARY_BUCKET_NAME]
    s3_object_args = ['--s3-object', ARBITRARY_OBJECT_NAME]
    all_args = dpa_name_args + s3_bucket_args + s3_object_args
    with mock.patch.object(dpa_calculator_main, "__name__", "__main__"):
        with mock.patch.object(sys, 'argv', sys.argv + all_args):
            dpa_calculator_main.init()


@then("the file uploaded to S3 should be")
def step_impl(context: ContextSas):
    s3 = boto3.client('s3')
    uploaded_file_local_filepath = 'tmp'
    s3.download_file(ARBITRARY_BUCKET_NAME, ARBITRARY_OBJECT_NAME, uploaded_file_local_filepath)
    output_content: str
    with open(uploaded_file_local_filepath, 'r') as f:
        output_content = f.read()
    Path(uploaded_file_local_filepath).unlink()
    expected_content = context.text.strip()
    assert output_content == expected_content, f'{output_content} != {expected_content}'
