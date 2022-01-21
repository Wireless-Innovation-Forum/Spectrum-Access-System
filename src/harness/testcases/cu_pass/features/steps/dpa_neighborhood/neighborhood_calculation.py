from functools import partial

from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloResults, AggregateInterferenceTypes
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.cbsd_deployer import \
    CbsdDeploymentOptions, NumberOfApsTypes, PopulationRetrieverTypes
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories
from testcases.cu_pass.features.helpers.utilities import get_expected_output_content, get_logging_file_handler, \
    sanitize_output_log
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.monte_carlo_iterations import \
    ContextMonteCarloIterations
from testcases.cu_pass.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher('parse')


class ContextNeighborhood(ContextDpa, ContextMonteCarloIterations):
    cbsd_deployment_options: CbsdDeploymentOptions
    number_of_iterations: int
    result: AggregateInterferenceMonteCarloResults


@step("{organization} interference")
def step_impl(context: ContextNeighborhood, organization: str):
    map = {
        'NTIA_2015': AggregateInterferenceTypes.NTIA,
        'WinnForum': AggregateInterferenceTypes.WinnForum
    }
    context.monte_carlo_runner = partial(context.monte_carlo_runner,
                                         aggregate_interference_calculator_type=map[organization])


@step("population by {population_type}")
def step_impl(context: ContextNeighborhood, population_type: str):
    map = {
        'census radius': PopulationRetrieverTypes.census,
        'region type': PopulationRetrieverTypes.region_type
    }
    context.cbsd_deployment_options.population_retriever_type = map[population_type]


@step("number of APs using {number_of_aps_type} analysis")
def step_impl(context: ContextNeighborhood, number_of_aps_type: str):
    map = {
        'ground based': NumberOfApsTypes.ground_based,
        'shipborne': NumberOfApsTypes.shipborne
    }
    context.cbsd_deployment_options.number_of_aps_calculator_class = map[number_of_aps_type]


@step("{number_of_aps:Integer} category {cbsd_category:CbsdCategory} APs")
def step_impl(context: ContextNeighborhood, number_of_aps: int, cbsd_category: CbsdCategories):
    context.cbsd_deployment_options.number_of_aps = context.cbsd_deployment_options.number_of_aps or {}
    context.cbsd_deployment_options.number_of_aps[cbsd_category] = number_of_aps


@when("the neighborhood radius is calculated")
def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    if not hasattr(context, 'dpa'):
        assign_arbitrary_dpa(context=context)
    simulation_results = context.monte_carlo_runner(dpa=context.dpa,
                                                    number_of_iterations=getattr(context, 'number_of_iterations', 1),
                                                    cbsd_deployment_options=context.cbsd_deployment_options).simulate()
    simulation_results.log()
    context.result = simulation_results


@then("the resulting distance should be {expected_distance:Integer}")
def step_impl(context: ContextNeighborhood, expected_distance: int):
    assert context.result.distance == expected_distance, f'{context.result.distance} != {expected_distance}'


@then("the resulting interference should be {expected_interference:Number}")
def step_impl(context: ContextNeighborhood, expected_interference: float):
    assert context.result.interference == expected_interference, f'{context.result.interference} != {expected_interference}'


@then("it should run without error")
def step_impl(context: ContextNeighborhood):
    pass


@then("the output log should be")
def step_impl(context: ContextNeighborhood):
    expected_content = get_expected_output_content(context=context)
    output_log_filepath = get_logging_file_handler().baseFilename
    output_content = sanitize_output_log(log_filepath=output_log_filepath)
    assert output_content == expected_content
