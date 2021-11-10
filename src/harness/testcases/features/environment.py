from glob import glob
from pathlib import Path
from runpy import run_path
from typing import Iterable, Union

from testcases.features import environment, steps
from testcases.features.helpers.utils import get_script_directory


def import_main_environment() -> None:
    environment_main_directory = get_script_directory(file=environment.__file__)
    environment_files = environment_main_directory.glob('[!_]*.py')
    _import_files(filepaths=environment_files)


def import_all_environments() -> None:
    steps_dir = get_script_directory(file=steps.__file__)
    any_environment_path = Path(steps_dir, '**', 'environment.py')
    all_environments = glob(str(any_environment_path))
    _import_files(filepaths=all_environments)


def _import_files(filepaths: Iterable[Union[str, Path]]) -> None:
    for environment_filepath in filepaths:
        run_path(str(environment_filepath))


import_main_environment()
import_all_environments()
