import boto3

from testcases.cu_pass.features.helpers.utilities import delete_file, sanitize_output_log
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

ARBITRARY_BUCKET_NAME = 'arbitrary_bucket_name'


def get_uploaded_log_content(context: ContextDocker) -> str:
    return get_uploaded_file_content(object_name=context.s3_object_name_log)


def get_uploaded_file_content(object_name: str) -> str:
    s3 = boto3.client('s3')
    uploaded_file_local_filepath = 'tmp'
    try:
        s3.download_file(ARBITRARY_BUCKET_NAME, object_name, uploaded_file_local_filepath)
        output_content = sanitize_output_log(log_filepath=uploaded_file_local_filepath)
    finally:
        delete_file(filepath=uploaded_file_local_filepath)
    return output_content
