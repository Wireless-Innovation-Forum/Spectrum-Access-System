import logging
from datetime import datetime
from glob import glob
from pathlib import Path
from runpy import run_path
from shutil import rmtree
from typing import Iterable, Union

from behave.model import Scenario

from testcases.cu_pass.features import environment, steps
from testcases.cu_pass.features.environment.hooks import antenna_gains_before_scenario, ContextSas, \
    interference_contribution_eirps_before_scenario, \
    set_context_sas_defaults, setup_monte_carlo_runner, total_interference_before_scenario, \
    transmitter_insertion_losses_before_scenario
from testcases.cu_pass.features.helpers.utilities import get_logging_file_handler, get_script_directory, \
    get_testing_logger, TESTING_LOGGER_FILE_HANDLER_NAME
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.contexts.context_docker import set_docker_context_defaults

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
    set_context_sas_defaults(context=context)

    if 'Total interference for a cbsd is calculated' in scenario.name:
        total_interference_before_scenario(context=context)
    elif 'Transmitter insertion losses' in scenario.name:
        transmitter_insertion_losses_before_scenario(context=context)
    elif 'antenna gains are calculated' in scenario.name:
        antenna_gains_before_scenario(context=context)
    elif 'Interference contribution EIRPs' in scenario.name:
        interference_contribution_eirps_before_scenario(context=context)
    elif scenario.feature.name == 'DPA Neighborhood' or 'Logging is captured' in scenario.name:
        setup_monte_carlo_runner(context=context)
    elif scenario.feature.name == 'Docker run':
        set_docker_context_defaults(context=context)

    _setup_logging(scenario=scenario)


def after_scenario(context: ContextSas, scenario: Scenario):
    if 'The DPA neighborhood is calculated' not in scenario.name:
        _cleanup_logging(scenario=scenario)


def _setup_logging(scenario: Scenario) -> None:
    logger = get_testing_logger()
    logging_path = _get_scenario_logging_path(scenario=scenario)
    logging_handler = logging.FileHandler(str(logging_path), 'w')
    logging_handler.set_name(TESTING_LOGGER_FILE_HANDLER_NAME)
    logger.addHandler(logging_handler)


def _get_scenario_logging_path(scenario: Scenario) -> Path:
    logging_directory = _get_scenario_logging_directory(scenario=scenario)
    logging_directory.mkdir(parents=True, exist_ok=True)
    return Path(logging_directory, f'{datetime.now().isoformat().replace(":", "-")}.log')


def _cleanup_logging(scenario: Scenario) -> None:
    logger = get_testing_logger()
    file_handler = get_logging_file_handler()
    logging_directory = _get_scenario_logging_directory(scenario=scenario)
    file_handler.close()
    logger.removeHandler(file_handler)
    rmtree(logging_directory, ignore_errors=True)


def _get_scenario_logging_directory(scenario: Scenario) -> Path:
    return Path(get_script_directory(__file__), 'logging', f'{scenario.name.replace(" ", "_").replace("@", "")}')
