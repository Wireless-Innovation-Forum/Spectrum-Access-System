from glob import glob
from pathlib import Path
from runpy import run_path
from typing import Iterable, Union

from behave.model import Scenario

from testcases.cu_pass.features import environment, steps
from testcases.cu_pass.features.environment.hooks import antenna_gains_before_scenario, ContextSas, \
    interference_contribution_eirps_before_scenario, neighborhood_calculation_before_scenario, \
    total_interference_before_scenario, transmitter_insertion_losses_before_scenario
from testcases.cu_pass.features.helpers.utils import get_script_directory

EXCLUDE_MANIFEST_FILES_GLOB = '[!_]*'
PYTHON_FILES_GLOB = f'{EXCLUDE_MANIFEST_FILES_GLOB}.py'


def steps_directory() -> Path:
    return get_script_directory(file=steps.__file__)


def all_environment_files() -> Iterable[str]:
    any_environment_path = Path(steps_directory(), '**', 'environment', '**', PYTHON_FILES_GLOB)
    return glob(str(any_environment_path), recursive=True)


def all_step_definitions() -> Iterable[str]:
    all_paths_in_steps_directory_glob = Path(steps_directory(), '**', PYTHON_FILES_GLOB)
    all_paths_in_steps_directory = glob(str(all_paths_in_steps_directory_glob), recursive=True)
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


def before_scenario(context: ContextSas, scenario: Scenario):
    if 'Total interference for a cbsd is calculated' in scenario.name:
        total_interference_before_scenario(context=context)
    elif 'The DPA neighborhood is calculated' in scenario.name:
        neighborhood_calculation_before_scenario(context=context)
    elif 'Transmitter insertion losses' in scenario.name:
        transmitter_insertion_losses_before_scenario(context=context)
    elif 'antenna gains are calculated' in scenario.name:
        antenna_gains_before_scenario(context=context)
    elif 'Interference contribution EIRPs' in scenario.name:
        interference_contribution_eirps_before_scenario(context=context)


def before_tag(context: ContextSas, tag: str):
    if tag == 'integration':
        context.with_integration = context.config.userdata.get('integration') == 'true'
