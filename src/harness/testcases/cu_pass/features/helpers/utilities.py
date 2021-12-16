import os
from pathlib import Path


def get_script_directory(file: str) -> Path:
    return Path(os.path.dirname(os.path.realpath(file)))
