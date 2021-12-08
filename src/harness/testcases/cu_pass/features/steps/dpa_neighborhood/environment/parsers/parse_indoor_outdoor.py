import parse
from behave import *

use_step_matcher("parse")

INDOOR_STRING = 'indoor'
OUTDOOR_STRING = 'outdoor'


@parse.with_pattern(rf'({INDOOR_STRING}|{OUTDOOR_STRING}) ?')
def parse_is_indoor(text: str) -> bool:
    return text.strip() == INDOOR_STRING


register_type(IsIndoor=parse_is_indoor)
