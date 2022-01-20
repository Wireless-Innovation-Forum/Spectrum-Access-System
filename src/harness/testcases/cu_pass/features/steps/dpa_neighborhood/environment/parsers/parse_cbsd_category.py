import parse
from behave import register_type

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdCategories


@parse.with_pattern("[AB]")
def parse_cbsd_category(cbsd_category_input: str) -> CbsdCategories:
    if cbsd_category_input == CbsdCategories.A.name:
        return CbsdCategories.A
    elif cbsd_category_input == CbsdCategories.B.name:
        return CbsdCategories.B
    else:
        raise NotImplementedError


register_type(CbsdCategory=parse_cbsd_category)
