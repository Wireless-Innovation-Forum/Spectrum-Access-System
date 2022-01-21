from dataclasses import dataclass

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    cbsd_creation_step, ContextCbsdCreation

use_step_matcher("parse")


@dataclass
class ContextNumberOfUes(ContextCbsdCreation):
    pass


@then("there should be {number_of_ues_per_ap:Integer} times as many CBSDs as if category {cbsd_category} AP CBSDs were created")
def step_impl(context: ContextNumberOfUes, number_of_ues_per_ap: int, cbsd_category: str):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_ue_grants = len(context.cbsds)
    cbsd_creation_step(context=context, cbsd_category=cbsd_category, is_user_equipment='AP')
    number_of_ap_grants = len(context.cbsds)
    assert number_of_ue_grants == number_of_ues_per_ap * number_of_ap_grants, \
        f'{number_of_ue_grants / number_of_ap_grants} != {number_of_ues_per_ap}'
