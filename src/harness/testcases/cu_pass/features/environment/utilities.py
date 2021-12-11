import logging


def get_logging_file_handler() -> logging.FileHandler:
    return logging.root.handlers[0]
