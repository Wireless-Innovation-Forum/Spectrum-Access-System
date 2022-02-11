from cu_pass.dpa_calculator.utilities import get_bearing_between_two_points, get_dpa_center
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.cbsd_creation.common_steps.cbsd_creation import \
    ContextCbsdCreation


def add_bearings_to_context(context: ContextCbsdCreation) -> None:
    context.bearings = [get_bearing_between_two_points(point1=get_dpa_center(dpa=context.dpa), point2=cbsd.location)
                        for cbsd in context.cbsds]
