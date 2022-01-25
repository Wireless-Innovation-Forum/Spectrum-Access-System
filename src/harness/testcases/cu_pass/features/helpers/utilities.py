import logging
import os
from pathlib import Path

from cu_pass.dpa_calculator.constants import DPA_CALCULATOR_LOGGER_NAME
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger
from testcases.cu_pass.features.environment.hooks import ContextSas


TESTING_LOGGER_FILE_HANDLER_NAME = 'testing_file_handler'


def delete_file(filepath: str) -> None:
    try:
        Path(filepath).unlink()
    except FileNotFoundError:
        pass


def get_testing_logger() -> logging.Logger:
    return get_dpa_calculator_logger()


def get_logging_file_handler() -> logging.FileHandler:
    logger = get_testing_logger()
    file_handler_logger = next(handler for handler in logger.handlers
                               if handler.get_name() == TESTING_LOGGER_FILE_HANDLER_NAME)
    return file_handler_logger


def get_expected_output_content(context: ContextSas) -> str:
    return sanitize_multiline_expected_string(content=context.text)


def get_script_directory(file: str) -> Path:
    return Path(os.path.dirname(os.path.realpath(file)))


def read_file(filepath: str) -> str:
    with open(filepath) as f:
        return f.read()


def sanitize_multiline_expected_string(content: str) -> str:
    return content.replace('    ', '\t').replace('\r', '')


def sanitize_output_log(log_filepath: str) -> str:
    with open(log_filepath) as f:
        lines = f.readlines()
        sanitized_lines = [line for line in lines
                           if 'Loaded climate data' not in line
                           and 'Loaded refractivity data' not in line
                           and 'Runtime' not in line
                           and 'Found credentials in environment variables.' not in line]
        return ''.join(sanitized_lines)
