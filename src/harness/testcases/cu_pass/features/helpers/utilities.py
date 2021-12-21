import os
from pathlib import Path


def get_script_directory(file: str) -> Path:
    return Path(os.path.dirname(os.path.realpath(file)))


def read_file(filepath: str) -> str:
    with open(filepath) as f:
        return f.read()
