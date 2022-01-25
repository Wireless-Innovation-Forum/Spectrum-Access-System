from typing import Optional

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher("cfparse")


@then("the category {cbsd_category:CbsdCategory} {is_indoor:IsIndoor?} antenna EIRPs should be {expected_power:Number} dBm")
def step_impl(context: ContextCbsdInterference, cbsd_category: CbsdCategories, is_indoor: Optional[bool], expected_power: int):
    """
    Args:
        context (behave.runner.Context):
        is_indoor (str):
        expected_power (str):
    """
    cbsd_numbers = (cbsd_number for cbsd_number, cbsd in enumerate(context.cbsds)
                    if is_indoor is None or cbsd.is_indoor == is_indoor
                    and cbsd.cbsd_category == cbsd_category)
    interference_contributions = (context.interference_components[cbsd_number] for cbsd_number in cbsd_numbers)
    eirps = [contribution.eirp for contribution in interference_contributions]
    assert all(eirp == expected_power for eirp in eirps)
