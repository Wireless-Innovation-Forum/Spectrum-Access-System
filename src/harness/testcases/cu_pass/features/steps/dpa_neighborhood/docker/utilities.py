import glob
from pathlib import Path
from typing import List, Optional, Tuple

import boto3

from testcases.cu_pass.features.helpers.utilities import delete_file, sanitize_output_log


def get_uploaded_log_content(bucket_name: str, object_name: str) -> str:
    return get_uploaded_file_content(bucket_name=bucket_name, object_name=object_name)


def get_uploaded_file_content(bucket_name: str, object_name: str) -> str:
    s3 = boto3.client('s3')
    uploaded_file_local_filepath = 'tmp'
    try:
        matching_uploaded_name = _get_object_name_ignoring_runtime(bucket_name=bucket_name, object_name=object_name)
        assert matching_uploaded_name, f'File {object_name} not found'
        s3.download_file(bucket_name, matching_uploaded_name, uploaded_file_local_filepath)
        output_content = sanitize_output_log(log_filepath=uploaded_file_local_filepath)
    finally:
        delete_file(filepath=uploaded_file_local_filepath)
    return output_content


def _get_object_name_ignoring_runtime(bucket_name: str, object_name: str) -> Optional[str]:
    object_name_without_runtime = get_filepath_without_runtime(filepath=object_name)
    uploaded_names = get_s3_uploaded_filenames(bucket_name=bucket_name)
    for uploaded_name in uploaded_names:
        uploaded_name_without_runtime = get_filepath_without_runtime(filepath=uploaded_name)
        if object_name_without_runtime == uploaded_name_without_runtime:
            return uploaded_name


def get_filepath_with_any_runtime(filepath: str) -> str:
    parts = _get_parts_without_runtime(filepath=filepath)
    parts_without_runtime = Path(*parts[0], '*', parts[1])
    return glob.glob(str(parts_without_runtime))[0]


def get_filepath_without_runtime(filepath: str) -> str:
    parts = _get_parts_without_runtime(filepath=filepath)
    parts_without_runtime = Path(*parts[0], parts[1])
    return str(parts_without_runtime)


def _get_parts_without_runtime(filepath: str) -> Tuple[Tuple[str, ...], str]:
    parts = Path(filepath).parts
    return parts[:-2], parts[-1]


def get_s3_uploaded_filenames(bucket_name: str) -> List[str]:
    s3 = boto3.client('s3')
    uploaded_contents = s3.list_objects(Bucket=bucket_name).get('Contents', [])
    return [key['Key'] for key in uploaded_contents]
