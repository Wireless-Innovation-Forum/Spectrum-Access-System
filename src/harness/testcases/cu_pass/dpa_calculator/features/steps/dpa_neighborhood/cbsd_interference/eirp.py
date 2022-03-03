from typing import List, Optional

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ContextCbsdInterference

use_step_matcher("cfparse")


@then("the category {cbsd_category:CbsdCategory?} {is_indoor:IsIndoor?} antenna EIRPs should be {expected_powers:FractionalDistribution} dBm")
def step_impl(context: ContextCbsdInterference, cbsd_category: CbsdCategories, is_indoor: Optional[bool], expected_powers: List[FractionalDistribution]):
    """
    Args:
        context (behave.runner.Context):
        is_indoor (str):
        expected_power (str):
    """
    cbsd_numbers = (cbsd_number for cbsd_number, cbsd in enumerate(context.cbsds)
                    if (is_indoor is None or cbsd.is_indoor == is_indoor)
                    and (not cbsd_category or cbsd.cbsd_category == cbsd_category))
    interference_contributions = (context.interference_components[cbsd_number] for cbsd_number in cbsd_numbers)
    eirps = [contribution.eirp for contribution in interference_contributions]
    for expected_power in expected_powers:
        expected_power.assert_data_matches_distribution(data=eirps)
