from dataclasses import dataclass
from math import isclose

from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfCbsdsCalculatorOptions
from cu_pass.dpa_calculator.utilities import get_dpa_center, get_region_type
from testcases.cu_pass.features.environment.global_parsers import parse_integer
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    cbsd_creation_step, ContextCbsdCreation

ARBITRARY_LARGE_POPULATION = 1000000

use_step_matcher("parse")


@dataclass
class ContextNumberOfUes(ContextCbsdCreation):
    pass


@given("{number_of_ues_per_ap} UEs per category {cbsd_category:CbsdCategory} AP")
def step_impl(context: ContextNumberOfUes, number_of_ues_per_ap: str, cbsd_category: CbsdCategories):
    context.number_of_cbsds_calculator_options = NumberOfCbsdsCalculatorOptions()
    if number_of_ues_per_ap == 'default':
        context.cbsd_deployment_options = CbsdDeploymentOptions(
            population_override=ARBITRARY_LARGE_POPULATION
        )
    else:
        number_of_ues_per_ap = parse_integer(text=number_of_ues_per_ap)
        region_type = get_region_type(get_dpa_center(context.dpa))
        context.number_of_cbsds_calculator_options.number_of_ues_per_ap_by_region_type[cbsd_category][
            region_type] = number_of_ues_per_ap


@then("there should be {number_of_ues_per_ap:Integer} times as many CBSDs as if category {cbsd_category} AP CBSDs were created")
def step_impl(context: ContextNumberOfUes, number_of_ues_per_ap: int, cbsd_category: str):
    """
    Args:
        context (behave.runner.Context):
    """
    number_of_ue_grants = len(context.cbsds)
    cbsd_creation_step(context=context, cbsd_category=cbsd_category, is_user_equipment='AP')
    number_of_ap_grants = len(context.cbsds)
    assert isclose(number_of_ue_grants / number_of_ap_grants, number_of_ues_per_ap, abs_tol=0.001), \
        f'{number_of_ue_grants / number_of_ap_grants} != {number_of_ues_per_ap}'
