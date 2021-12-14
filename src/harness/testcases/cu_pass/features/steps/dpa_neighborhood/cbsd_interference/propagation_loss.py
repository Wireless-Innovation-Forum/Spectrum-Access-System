from behave import *

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.constants import REGION_TYPE_RURAL
from dpa_calculator.utilities import Point
from testcases.cu_pass.features.steps.dpa_neighborhood.cbsd_interference.environment.environment import \
    ARBITRARY_EIRP_MAXIMUM, ContextCbsdInterference
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import REGION_TYPE_TO_DPA_NAME_MAP
from testcases.cu_pass.features.steps.dpa_neighborhood.environment.utilities import add_bearings_to_context

use_step_matcher('parse')


@step('a CBSD at a location with larger {larger_loss_model} with height {height_in_meters:Integer}')
def step_impl(context: ContextCbsdInterference, larger_loss_model: str, height_in_meters: int):
    if context.dpa.name == REGION_TYPE_TO_DPA_NAME_MAP[REGION_TYPE_RURAL]:
        coordinates = Point(latitude=33.19313987787715, longitude=-96.36484196127637)
    elif larger_loss_model == 'ITM':
        coordinates = Point(latitude=40.19146905688054, longitude=-76.13331647039989)
    else:
        coordinates = Point(latitude=39.78257723575214, longitude=-75.81383219225971)
    context.cbsds = [Cbsd(eirp_maximum=ARBITRARY_EIRP_MAXIMUM, height_in_meters=height_in_meters, location=coordinates)]
    add_bearings_to_context(context=context)


@then('the propagation loss should be {expected_loss:Number}')
def step_impl(context: ContextCbsdInterference, expected_loss: float):
    actual_loss = context.interference_components[0].loss_propagation
    assert actual_loss == expected_loss, f'{actual_loss} != {expected_loss}'
