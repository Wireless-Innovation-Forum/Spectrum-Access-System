from typing import Optional

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions, NEIGHBORHOOD_DISTANCES_TYPE
from testcases.cu_pass.features.environment.hooks import ContextSas


class ContextCbsdDeploymentOptions(ContextSas):
    cbsd_deployment_options: CbsdDeploymentOptions


def get_current_cbsd_deployment_options(context: ContextCbsdDeploymentOptions,
                                        default: Optional[CbsdDeploymentOptions] = CbsdDeploymentOptions()) -> CbsdDeploymentOptions:
    context.cbsd_deployment_options = getattr(context, 'cbsd_deployment_options', default)
    return context.cbsd_deployment_options


def get_current_simulation_distances(context: ContextCbsdDeploymentOptions, default: Optional[NEIGHBORHOOD_DISTANCES_TYPE] = None) -> NEIGHBORHOOD_DISTANCES_TYPE:
    default_cbsd_deployment_options = CbsdDeploymentOptions()
    if default is not None:
        default_cbsd_deployment_options.simulation_distances_in_kilometers = default
    current_cbsd_deployment_options = get_current_cbsd_deployment_options(context=context, default=default_cbsd_deployment_options)
    return current_cbsd_deployment_options.simulation_distances_in_kilometers
