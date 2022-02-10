import re

import parse
from behave import register_type

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.dpa_calculator.features.environment.global_parsers import get_list_regex

CBSD_CATEGORY_REGEX = r"[AB]"


@parse.with_pattern(CBSD_CATEGORY_REGEX)
def parse_cbsd_category(cbsd_category_input: str) -> CbsdCategories:
    if cbsd_category_input == CbsdCategories.A.name:
        return CbsdCategories.A
    elif cbsd_category_input == CbsdCategories.B.name:
        return CbsdCategories.B
    else:
        raise NotImplementedError


@parse.with_pattern(get_list_regex(item_regex=CBSD_CATEGORY_REGEX))
def parse_cbsd_category_list(text: str):
    categories_text = re.compile(f'({CBSD_CATEGORY_REGEX})').findall(text)
    return [parse_cbsd_category(cbsd_category_input=category_text[0]) for category_text in categories_text]


register_type(CbsdCategory=parse_cbsd_category)
register_type(CbsdCategoryList=parse_cbsd_category_list)
