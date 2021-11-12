from glob import glob
from pathlib import Path
from runpy import run_path
from typing import Iterable, Union

from testcases.cu_pass.features import environment, steps
from testcases.cu_pass.features.helpers.utils import get_script_directory

EXCLUDE_MANIFEST_FILES_GLOB = '[!_]*'
PYTHON_FILES_GLOB = f'{EXCLUDE_MANIFEST_FILES_GLOB}.py'


def steps_directory() -> Path:
    return get_script_directory(file=steps.__file__)


def all_environment_files() -> Iterable[str]:
    any_environment_path = Path(steps_directory(), '**', 'environment', EXCLUDE_MANIFEST_FILES_GLOB)
    return glob(str(any_environment_path))


def all_step_definitions() -> Iterable[str]:
    all_paths_in_steps_directory_glob = Path(steps_directory(), '**', PYTHON_FILES_GLOB)
    all_paths_in_steps_directory = glob(str(all_paths_in_steps_directory_glob))
    return set(all_paths_in_steps_directory) - set(all_environment_files())


def import_main_environment() -> None:
    environment_main_directory = get_script_directory(file=environment.__file__)
    environment_files = environment_main_directory.glob(PYTHON_FILES_GLOB)
    _import_files(filepaths=environment_files)


def import_all_environments() -> None:
    _import_files(filepaths=all_environment_files())


def import_all_step_definitions() -> None:
    _import_files(filepaths=all_step_definitions())


def _import_files(filepaths: Iterable[Union[str, Path]]) -> None:
    for environment_filepath in filepaths:
        run_path(str(environment_filepath))


import_main_environment()
import_all_environments()
import_all_step_definitions()
