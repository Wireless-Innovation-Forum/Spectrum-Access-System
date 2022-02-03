import parse
from behave import register_type

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes


@parse.with_pattern("(AP|UE)s?")
def parse_cbsd_type(text: str) -> CbsdTypes:
    text = text.replace('s', '')
    if text == CbsdTypes.AP.name:
        return CbsdTypes.AP
    elif text == CbsdTypes.UE.name:
        return CbsdTypes.UE
    else:
        raise NotImplementedError


register_type(CbsdType=parse_cbsd_type)
