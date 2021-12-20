from pathlib import Path

import boto3
from behave import *
from moto import mock_s3

from testcases.cu_pass.features.environment.hooks import ContextSas

use_step_matcher("parse")


ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'
ARBITRARY_OBJECT_NAME = 'arbitrary_object_name'


@fixture
def _mock_s3(context: ContextSas) -> None:
    with mock_s3():
        yield


@when("the main docker command is run")
def step_impl(context: ContextSas):
    use_fixture(_mock_s3, context=context)
    output_log_filename = 'output_log_filename'
    # mock.patch.dict(os.environ, AWS_ACCESS_KEY_ID='AWS_ACCESS_KEY_ID', AWS_SECRET_ACCESS_KEY='AWS_SECRET_ACCESS_KEY')
    with open(output_log_filename, 'w') as f:
        f.write('content')
    s3_client = boto3.client('s3')
    s3_client.create_bucket(Bucket=ARBITRARY_BUCKET_NAME)
    response = s3_client.upload_file(output_log_filename, ARBITRARY_BUCKET_NAME, ARBITRARY_OBJECT_NAME)
    Path(output_log_filename).unlink()
    # subprocess.run('python3 src/harness/cu_pass/dpa_calculator/main')


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
