from typing import Optional

from behave import *

from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher("cfparse")


@then("the {is_indoor:IsIndoor?} antenna EIRPs should be {expected_power:Number} dBm")
def step_impl(context: ContextCbsdInterference, is_indoor: Optional[bool], expected_power: int):
    """
    Args:
        context (behave.runner.Context):
        is_indoor (str):
        expected_power (str):
    """
    cbsd_numbers = (cbsd_number for cbsd_number, cbsd in enumerate(context.cbsds)
                    if is_indoor is None or cbsd.is_indoor == is_indoor)
    interference_contributions = (context.interference_components[cbsd_number] for cbsd_number in cbsd_numbers)
    assert all(contribution.eirp == expected_power for contribution in interference_contributions)
