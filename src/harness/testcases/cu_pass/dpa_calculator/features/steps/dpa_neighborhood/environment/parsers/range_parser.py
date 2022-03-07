from behave import *

from cu_pass.dpa_calculator.helpers.parsers import parse_number_range

register_type(NumberRange=parse_number_range)
