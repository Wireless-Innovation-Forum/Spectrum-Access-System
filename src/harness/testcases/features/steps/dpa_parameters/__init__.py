from os.path import basename, isfile

from testcases.features.helpers.utils import get_script_directory

SCRIPT_DIR = get_script_directory(file=__file__)

modules = SCRIPT_DIR.glob('[!_]*.py')
__all__ = [basename(f)[:-3] for f in modules if isfile(f)]

