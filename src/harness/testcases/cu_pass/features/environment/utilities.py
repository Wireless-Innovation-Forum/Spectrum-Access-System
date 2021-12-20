import logging

from testcases.cu_pass.features.environment.hooks import ContextSas


def get_logging_file_handler() -> logging.FileHandler:
    return logging.root.handlers[0]


def get_expected_output_content(context: ContextSas) -> str:
    return context.text.replace('    ', '\t').replace('\r', '')


def sanitize_output_log(log_filepath: str) -> str:
    with open(log_filepath) as f:
        lines = f.readlines()
        sanitized_lines = [line for line in lines
                           if 'Loaded climate data' not in line
                           and 'Loaded refractivity data' not in line
                           and 'Runtime' not in line
                           and 'Found credentials in environment variables.' not in line]
        return ''.join(sanitized_lines)
