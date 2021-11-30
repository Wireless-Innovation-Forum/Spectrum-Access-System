import parse
from behave import *

from reference_models.dpa.dpa_mgr import BuildDpa


@parse.with_pattern('.*')
def parse_dpa(text: str):
    return BuildDpa(dpa_name=text.upper())


register_type(Dpa=parse_dpa)
